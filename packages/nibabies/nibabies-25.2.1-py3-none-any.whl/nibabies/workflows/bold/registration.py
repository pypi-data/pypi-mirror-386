# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Registration workflows
++++++++++++++++++++++

.. autofunction:: init_bold_reg_wf
.. autofunction:: init_bold_t1_trans_wf
.. autofunction:: init_bbreg_wf
.. autofunction:: init_fsl_bbr_wf

"""

import logging
import os
import typing as ty

from nipype.interfaces import c3, fsl
from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

from nibabies import config, data
from nibabies._types import AffineDOF, RegistrationInit

DEFAULT_MEMORY_MIN_GB = config.DEFAULT_MEMORY_MIN_GB
LOGGER = logging.getLogger('nipype.workflow')


def init_bold_reg_wf(
    freesurfer: bool,
    use_bbr: bool,
    bold2anat_dof: AffineDOF,
    bold2anat_init: RegistrationInit,
    mem_gb: float,
    omp_nthreads: int,
    name: str = 'bold_reg_wf',
    sloppy: bool = False,
):
    """
    Build a workflow to run same-subject, BOLD-to-anat image-registration.

    Calculates the registration between a reference BOLD image and anatomical-space
    using a boundary-based registration (BBR) cost function.
    If FreeSurfer-based preprocessing is enabled, the ``bbregister`` utility
    is used to align the BOLD images to the reconstructed subject, and the
    resulting transform is adjusted to target the anatomical space.
    If FreeSurfer-based preprocessing is disabled, FSL FLIRT is used with the
    BBR cost function to directly target the T1 space.

    Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes

            from fmriprep.workflows.bold.registration import init_bold_reg_wf
            wf = init_bold_reg_wf(freesurfer=True,
                                  mem_gb=3,
                                  omp_nthreads=1,
                                  use_bbr=True,
                                  bold2anat_dof=9,
                                  bold2anat_init='auto')

    Parameters
    ----------
    freesurfer : :obj:`bool`
        Enable FreeSurfer functional registration (bbregister)
    use_bbr : :obj:`bool` or None
        Enable/disable boundary-based registration refinement.
        If ``None``, test BBR result for distortion before accepting.
    bold2anat_dof : 6, 9 or 12
        Degrees-of-freedom for BOLD-anatomical registration
    bold2anat_init : str, 't1w', 't2w' or 'header'
        If ``'header'``, use header information for initialization of BOLD and T1 images.
        If ``'t1w'``, align BOLD to T1w by their centers.
        If ``'t2w'``, align BOLD to T1w using the T2w as an intermediate.
    mem_gb : :obj:`float`
        Size of BOLD file in GB
    omp_nthreads : :obj:`int`
        Maximum number of threads an individual process may use
    name : :obj:`str`
        Name of workflow (default: ``bold_reg_wf``)

    Inputs
    ------
    ref_bold_brain
        Reference image to which BOLD series is aligned
        If ``fieldwarp == True``, ``ref_bold_brain`` should be unwarped
    anat_preproc
        Anatomical reference volume
    anat_brain
        Skull-stripped ``anat_preproc``
    anat_dseg
        Segmentation of preprocessed structural image, including
        gray-matter (GM), white-matter (WM) and cerebrospinal fluid (CSF)
    subjects_dir
        FreeSurfer SUBJECTS_DIR
    subject_id
        FreeSurfer subject ID
    fsnative2anat_xfm
        LTA-style affine matrix translating from FreeSurfer-conformed subject space to anatomical

    Outputs
    -------
    itk_bold_to_anat
        Affine transform from ``ref_bold_brain`` to anatomical space (ITK format)
    itk_anat_to_bold
        Affine transform from anatomical space to BOLD space (ITK format)
    fallback
        Boolean indicating whether BBR was rejected (mri_coreg registration returned)

    See Also
    --------
      * :py:func:`~fmriprep.workflows.bold.registration.init_bbreg_wf`
      * :py:func:`~fmriprep.workflows.bold.registration.init_fsl_bbr_wf`

    """
    from niworkflows.engine.workflows import LiterateWorkflow as Workflow

    workflow = Workflow(name=name)
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                'ref_bold_brain',
                'anat_preproc',
                'anat_mask',
                'anat_dseg',
                'subjects_dir',
                'subject_id',
                'fsnative2anat_xfm',
            ]
        ),
        name='inputnode',
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['itk_bold_to_anat', 'itk_anat_to_bold', 'fallback']),
        name='outputnode',
    )

    if freesurfer:
        bbr_wf = init_bbreg_wf(
            use_bbr=use_bbr,
            bold2anat_dof=bold2anat_dof,
            bold2anat_init=bold2anat_init,
            omp_nthreads=omp_nthreads,
        )
    else:
        bbr_wf = init_fsl_bbr_wf(
            use_bbr=use_bbr,
            bold2anat_dof=bold2anat_dof,
            bold2anat_init=bold2anat_init,
            sloppy=sloppy,
            omp_nthreads=omp_nthreads,
        )

    # fmt: off
    workflow.connect([
        (inputnode, bbr_wf, [
            ('ref_bold_brain', 'inputnode.in_file'),
            ('fsnative2anat_xfm', 'inputnode.fsnative2anat_xfm'),
            ('subjects_dir', 'inputnode.subjects_dir'),
            ('subject_id', 'inputnode.subject_id'),
            ('anat_preproc', 'inputnode.anat_preproc'),
            ('anat_mask', 'inputnode.anat_mask'),
            ('anat_dseg', 'inputnode.anat_dseg'),
        ]),
        (bbr_wf, outputnode, [
            ('outputnode.itk_bold_to_anat', 'itk_bold_to_anat'),
            ('outputnode.itk_anat_to_bold', 'itk_anat_to_bold'),
            ('outputnode.fallback', 'fallback'),
        ]),
    ])  # fmt:skip

    return workflow


def init_bbreg_wf(
    use_bbr: bool,
    bold2anat_dof: AffineDOF,
    bold2anat_init: RegistrationInit,
    omp_nthreads: int,
    name: str = 'bbreg_wf',
):
    """
    Build a workflow to run FreeSurfer's ``bbregister``.

    This workflow uses FreeSurfer's ``bbregister`` to register a BOLD image to
    a T2-weighted or T1-weighted structural image.

    It is a counterpart to :py:func:`~fmriprep.workflows.bold.registration.init_fsl_bbr_wf`,
    which performs the same task using FSL's FLIRT with a BBR cost function.
    The ``use_bbr`` option permits a high degree of control over registration.
    If ``False``, standard, affine coregistration will be performed using
    FreeSurfer's ``mri_coreg`` tool.
    If ``True``, ``bbregister`` will be seeded with the initial transform found
    by ``mri_coreg`` (equivalent to running ``bbregister --init-coreg``).
    If ``None``, after ``bbregister`` is run, the resulting affine transform
    will be compared to the initial transform found by ``mri_coreg``.
    Excessive deviation will result in rejecting the BBR refinement and
    accepting the original, affine registration.

    Workflow Graph
        .. workflow ::
            :graph2use: orig
            :simple_form: yes

            from nibabies.workflows.bold.registration import init_bbreg_wf
            wf = init_bbreg_wf(use_bbr=True, bold2anat_dof=9,
                               bold2anat_init='t1w', omp_nthreads=1)


    Parameters
    ----------
    use_bbr : :obj:`bool` or None
        Enable/disable boundary-based registration refinement.
        If ``None``, test BBR result for distortion before accepting.
    bold2anat_dof : 6, 9 or 12
        Degrees-of-freedom for BOLD-anatomical registration
    bold2anat_init : str, 't1w', 't2w' or 'header'
        If ``'header'``, use header information for initialization of BOLD and T1 images.
        If ``'t1w'``, align BOLD to T1w by their centers.
        If ``'t2w'``, align BOLD to T1w using the T2w as an intermediate.
    name : :obj:`str`, optional
        Workflow name (default: bbreg_wf)

    Inputs
    ------
    in_file
        Reference BOLD image to be registered
    fsnative2anat_xfm
        FSL-style affine matrix translating from either
        FreeSurfer T1.mgz to T1w or T2.mgz to T2w
    subjects_dir
        FreeSurfer SUBJECTS_DIR
    subject_id
        FreeSurfer subject ID (must have folder in SUBJECTS_DIR)
    anat_preproc
        Unused (see :py:func:`~fmriprep.workflows.bold.registration.init_fsl_bbr_wf`)
    anat_mask
        Unused (see :py:func:`~fmriprep.workflows.bold.registration.init_fsl_bbr_wf`)
    anat_dseg
        Unused (see :py:func:`~fmriprep.workflows.bold.registration.init_fsl_bbr_wf`)

    Outputs
    -------
    itk_bold_to_anat
        Affine transform from ``ref_bold_brain`` to anatomical space (ITK format)
    itk_anat_to_bold
        Affine transform from anatomical space to BOLD space (ITK format)
    fallback
        Boolean indicating whether BBR was rejected (mri_coreg registration returned)

    """
    from nipype.interfaces.freesurfer import BBRegister
    from niworkflows.engine.workflows import LiterateWorkflow as Workflow
    from niworkflows.interfaces.nitransforms import ConcatenateXFMs
    from niworkflows.interfaces.patches import FreeSurferSource

    from nibabies.interfaces.patches import MRICoreg

    workflow = Workflow(name=name)
    workflow.__desc__ = """\
The BOLD reference was then co-registered to the anatomical reference using
`bbregister` (FreeSurfer) which implements boundary-based registration [@bbr].
Co-registration was configured with {dof} degrees of freedom{reason}.
""".format(
        dof={6: 'six', 9: 'nine', 12: 'twelve'}[bold2anat_dof],
        reason=(
            ''
            if bold2anat_dof == 6
            else 'to account for distortions remaining in the BOLD reference'
        ),
    )

    use_t2w = bold2anat_init == 't2w'
    if use_t2w:
        workflow.__desc__ += ' The aligned T2w image was used for initial co-registration.'

    inputnode = pe.Node(
        niu.IdentityInterface(
            [
                'in_file',
                'fsnative2anat_xfm',  # BBRegister
                'subjects_dir',
                'subject_id',
                'anat_preproc',  # FLIRT BBR
                'anat_mask',
                'anat_dseg',
            ]
        ),
        name='inputnode',
    )
    outputnode = pe.Node(
        niu.IdentityInterface(['itk_bold_to_anat', 'itk_anat_to_bold', 'fallback']),
        name='outputnode',
    )

    if bold2anat_init not in ty.get_args(RegistrationInit):
        raise ValueError(f'Unknown BOLD-to-anatomical initialization option: {bold2anat_init}')

    # For now make BBR unconditional - in the future, we can fall back to identity,
    # but adding the flexibility without testing seems a bit dangerous
    if bold2anat_init == 'header':
        if use_bbr is False:
            raise ValueError('Cannot disable BBR and use header registration')
        if use_bbr is None:
            LOGGER.warning('Initializing BBR with header; affine fallback disabled')
            use_bbr = True

    fssource = pe.Node(FreeSurferSource(), name='fssource')

    mri_coreg = pe.Node(
        MRICoreg(dof=bold2anat_dof, sep=[4], ftol=0.0001, linmintol=0.01),
        name='mri_coreg',
        n_procs=omp_nthreads,
        mem_gb=5,
    )
    if use_t2w:
        mri_coreg.inputs.reference_mask = False

    bbregister = pe.Node(
        BBRegister(
            dof=bold2anat_dof,
            contrast_type='t2',
            out_lta_file=True,
        ),
        name='bbregister',
        mem_gb=12,
    )
    if bold2anat_init == 'header':
        bbregister.inputs.init = 'header'

    transforms = pe.Node(niu.Merge(2), run_without_submitting=True, name='transforms')
    # In cases where Merge(2) only has `in1` or `in2` defined
    # output list will just contain a single element
    select_transform = pe.Node(
        niu.Select(index=0), run_without_submitting=True, name='select_transform'
    )
    merge_ltas = pe.Node(niu.Merge(2), name='merge_ltas', run_without_submitting=True)
    concat_xfm = pe.Node(ConcatenateXFMs(inverse=True), name='concat_xfm')

    workflow.connect([
        (inputnode, merge_ltas, [('fsnative2anat_xfm', 'in2')]),
        # Wire up the co-registration alternatives
        (transforms, select_transform, [('out', 'inlist')]),
        (select_transform, merge_ltas, [('out', 'in1')]),
        (merge_ltas, concat_xfm, [('out', 'in_xfms')]),
        (concat_xfm, outputnode, [('out_xfm', 'itk_bold_to_anat')]),
        (concat_xfm, outputnode, [('out_inv', 'itk_anat_to_bold')]),
    ])  # fmt:skip

    # Do not initialize with header, use mri_coreg
    if bold2anat_init != 'header':
        workflow.connect([
            (inputnode, mri_coreg, [('subjects_dir', 'subjects_dir'),
                                    ('subject_id', 'subject_id'),
                                    ('in_file', 'source_file')]),
            (mri_coreg, transforms, [('out_lta_file', 'in2')]),
        ])  # fmt:skip

        if use_t2w:
            workflow.connect([
                (inputnode, fssource, [('subjects_dir', 'subjects_dir'),
                                       ('subject_id', 'subject_id')]),
                (fssource, mri_coreg, [('T2', 'reference_file')]),
            ])  # fmt:skip

        # Short-circuit workflow building, use initial registration
        if use_bbr is False:
            outputnode.inputs.fallback = True

            return workflow

        # Otherwise bbregister will also be used
        workflow.connect(mri_coreg, 'out_lta_file', bbregister, 'init_reg_file')

    # Use bbregister
    workflow.connect([
        (inputnode, bbregister, [('subjects_dir', 'subjects_dir'),
                                 ('subject_id', 'subject_id'),
                                 ('in_file', 'source_file')]),
        (bbregister, transforms, [('out_lta_file', 'in1')]),
    ])  # fmt:skip

    # Short-circuit workflow building, use boundary-based registration
    if use_bbr is True:
        outputnode.inputs.fallback = False

        return workflow

    # Only reach this point if bold2anat_init is "t1w" or "t2w" and use_bbr is None
    compare_transforms = pe.Node(niu.Function(function=compare_xforms), name='compare_transforms')

    workflow.connect([
        (transforms, compare_transforms, [('out', 'lta_list')]),
        (compare_transforms, outputnode, [('out', 'fallback')]),
        (compare_transforms, select_transform, [('out', 'index')]),
    ])  # fmt:skip

    return workflow


def init_fsl_bbr_wf(
    use_bbr: bool,
    bold2anat_dof: AffineDOF,
    bold2anat_init: RegistrationInit,
    omp_nthreads: int,
    sloppy: bool = False,
    name: str = 'fsl_bbr_wf',
):
    """
    Build a workflow to run FSL's ``flirt``.

    This workflow uses FSL FLIRT to register a BOLD image to an anatomical
    structural image, using a boundary-based registration (BBR) cost function.
    It is a counterpart to :py:func:`~fmriprep.workflows.bold.registration.init_bbreg_wf`,
    which performs the same task using FreeSurfer's ``bbregister``.

    The ``use_bbr`` option permits a high degree of control over registration.
    If ``False``, standard, rigid coregistration will be performed by FLIRT.
    If ``True``, FLIRT-BBR will be seeded with the initial transform found by
    the rigid coregistration.
    If ``None``, after FLIRT-BBR is run, the resulting affine transform
    will be compared to the initial transform found by FLIRT.
    Excessive deviation will result in rejecting the BBR refinement and
    accepting the original, affine registration.

    Workflow Graph
        .. workflow ::
            :graph2use: orig
            :simple_form: yes

            from fmriprep.workflows.bold.registration import init_fsl_bbr_wf
            wf = init_fsl_bbr_wf(
                use_bbr=True, bold2anat_dof=9, bold2anat_init='t1w', omp_nthreads=1
            )


    Parameters
    ----------
    use_bbr : :obj:`bool` or None
        Enable/disable boundary-based registration refinement.
        If ``None``, test BBR result for distortion before accepting.
    bold2anat_dof : 6, 9 or 12
        Degrees-of-freedom for BOLD-anatomical registration
    bold2anat_init : str, 't1w', 't2w' or 'header'
        If ``'header'``, use header information for initialization of BOLD and T1 images.
        If ``'t1w'``, align BOLD to T1w by their centers.
        If ``'t2w'``, align BOLD to T1w using the T2w as an intermediate.
    name : :obj:`str`, optional
        Workflow name (default: fsl_bbr_wf)

    Inputs
    ------
    in_file
        Reference BOLD image to be registered
    anat_preproc
        Anatomical structural image
    anat_mask
        Brain mask of structural image
    anat_dseg
        FAST segmentation of masked ``t1w_preproc``
    fsnative2anat_xfm
        Unused (see :py:func:`~fmriprep.workflows.bold.registration.init_bbreg_wf`)
    subjects_dir
        Unused (see :py:func:`~fmriprep.workflows.bold.registration.init_bbreg_wf`)
    subject_id
        Unused (see :py:func:`~fmriprep.workflows.bold.registration.init_bbreg_wf`)

    Outputs
    -------
    itk_bold_to_anat
        Affine transform from ``ref_bold_brain`` to anatomical space (ITK format)
    itk_anat_to_bold
        Affine transform from anatomical space to BOLD space (ITK format)
    fallback
        Boolean indicating whether BBR was rejected (rigid FLIRT registration returned)

    """
    from nipype.interfaces.freesurfer import MRICoreg
    from niworkflows.engine.workflows import LiterateWorkflow as Workflow
    from niworkflows.interfaces.freesurfer import PatchedLTAConvert as LTAConvert
    from niworkflows.interfaces.nibabel import ApplyMask
    from niworkflows.utils.images import dseg_label as _dseg_label

    workflow = Workflow(name=name)
    workflow.__desc__ = """\
The BOLD reference was then co-registered to the anatomical reference using
`mri_coreg` (FreeSurfer) followed by `flirt` [FSL {fsl_ver}, @flirt]
with the boundary-based registration [@bbr] cost-function.
Co-registration was configured with {dof} degrees of freedom{reason}.
""".format(
        fsl_ver=fsl.FLIRT().version or '<ver>',
        dof={6: 'six', 9: 'nine', 12: 'twelve'}[bold2anat_dof],
        reason=(
            ''
            if bold2anat_dof == 6
            else 'to account for distortions remaining in the BOLD reference'
        ),
    )

    inputnode = pe.Node(
        niu.IdentityInterface(
            [
                'in_file',
                'fsnative2anat_xfm',  # BBRegister
                'subjects_dir',
                'subject_id',
                'anat_preproc',  # FLIRT BBR
                'anat_mask',
                'anat_dseg',
            ]
        ),
        name='inputnode',
    )
    outputnode = pe.Node(
        niu.IdentityInterface(['itk_bold_to_anat', 'itk_anat_to_bold', 'fallback']),
        name='outputnode',
    )

    # TODO: This may change on whether T1/T2 is used as reference
    wm_mask = pe.Node(niu.Function(function=_dseg_label), name='wm_mask')
    wm_mask.inputs.label = 2  # BIDS default is WM=2

    if bold2anat_init not in ty.get_args(RegistrationInit):
        raise ValueError(f'Unknown BOLD-anat initialization option: {bold2anat_init}')

    if bold2anat_init == 'header':
        raise NotImplementedError('Header-based registration initialization not supported for FSL')

    if bold2anat_init == 't2w':
        LOGGER.warning(
            'T2w intermediate for FSL is not implemented, registering with T1w instead.'
        )

    # Mask T1w_preproc with T1w_mask to make T1w_brain
    mask_anat_brain = pe.Node(ApplyMask(), name='mask_anat_brain')

    mri_coreg = pe.Node(
        MRICoreg(dof=bold2anat_dof, sep=[4], ftol=0.0001, linmintol=0.01),
        name='mri_coreg',
        n_procs=omp_nthreads,
        mem_gb=5,
    )

    lta_to_fsl = pe.Node(LTAConvert(out_fsl=True), name='lta_to_fsl', mem_gb=DEFAULT_MEMORY_MIN_GB)

    invt_bbr = pe.Node(
        fsl.ConvertXFM(invert_xfm=True), name='invt_bbr', mem_gb=DEFAULT_MEMORY_MIN_GB
    )

    # BOLD to anat transform matrix is from fsl, using c3 tools to convert to
    # something ANTs will like.
    fsl2itk_fwd = pe.Node(
        c3.C3dAffineTool(fsl2ras=True, itk_transform=True),
        name='fsl2itk_fwd',
        mem_gb=DEFAULT_MEMORY_MIN_GB,
    )
    fsl2itk_inv = pe.Node(
        c3.C3dAffineTool(fsl2ras=True, itk_transform=True),
        name='fsl2itk_inv',
        mem_gb=DEFAULT_MEMORY_MIN_GB,
    )
    # fmt:off
    workflow.connect([
        (inputnode, mask_anat_brain, [('anat_preproc', 'in_file'),
                                      ('anat_mask', 'in_mask')]),
        (inputnode, mri_coreg, [('in_file', 'source_file')]),
        (inputnode, fsl2itk_fwd, [('in_file', 'source_file')]),
        (inputnode, fsl2itk_inv, [('in_file', 'reference_file')]),
        (mask_anat_brain, mri_coreg, [('out_file', 'reference_file')]),
        (mask_anat_brain, fsl2itk_fwd, [('out_file', 'reference_file')]),
        (mask_anat_brain, fsl2itk_inv, [('out_file', 'source_file')]),
        (mri_coreg, lta_to_fsl, [('out_lta_file', 'in_lta')]),
        (invt_bbr, fsl2itk_inv, [('out_file', 'transform_file')]),
        (fsl2itk_fwd, outputnode, [('itk_transform', 'itk_bold_to_anat')]),
        (fsl2itk_inv, outputnode, [('itk_transform', 'itk_anat_to_bold')]),
    ])  # fmt:skip

    # Short-circuit workflow building, use rigid registration
    if use_bbr is False:
        # fmt:off
        workflow.connect([
            (lta_to_fsl, invt_bbr, [('out_fsl', 'in_file')]),
            (lta_to_fsl, fsl2itk_fwd, [('out_fsl', 'transform_file')]),
        ])
        # fmt:on
        outputnode.inputs.fallback = True

        return workflow

    flt_bbr = pe.Node(
        fsl.FLIRT(cost_func='bbr', dof=bold2anat_dof, args='-basescale 1'),
        name='flt_bbr',
    )

    FSLDIR = os.getenv('FSLDIR')
    if FSLDIR and os.path.exists(schedule := os.path.join(FSLDIR, 'etc/flirtsch/bbr.sch')):
        flt_bbr.inputs.schedule = schedule
    else:
        # Should mostly be hit while building docs
        LOGGER.warning('FSLDIR unset - using packaged BBR schedule')
        flt_bbr.inputs.schedule = data.load('flirtsch/bbr.sch')
    # fmt:off
    workflow.connect([
        (inputnode, wm_mask, [('anat_dseg', 'in_seg')]),
        (inputnode, flt_bbr, [('in_file', 'in_file')]),
        (lta_to_fsl, flt_bbr, [('out_fsl', 'in_matrix_file')]),
    ])
    # fmt:on
    if sloppy is True:
        downsample = pe.Node(
            niu.Function(
                function=_conditional_downsampling, output_names=['out_file', 'out_mask']
            ),
            name='downsample',
        )
        # fmt:off
        workflow.connect([
            (mask_anat_brain, downsample, [('out_file', 'in_file')]),
            (wm_mask, downsample, [('out', 'in_mask')]),
            (downsample, flt_bbr, [('out_file', 'reference'),
                                   ('out_mask', 'wm_seg')]),
        ])
        # fmt:on
    else:
        # fmt:off
        workflow.connect([
            (mask_anat_brain, flt_bbr, [('out_file', 'reference')]),
            (wm_mask, flt_bbr, [('out', 'wm_seg')]),
        ])
        # fmt:on

    # Short-circuit workflow building, use boundary-based registration
    if use_bbr is True:
        # fmt:off
        workflow.connect([
            (flt_bbr, invt_bbr, [('out_matrix_file', 'in_file')]),
            (flt_bbr, fsl2itk_fwd, [('out_matrix_file', 'transform_file')]),
        ])
        # fmt:on
        outputnode.inputs.fallback = False

        return workflow

    # Reached only if use_bbr is None
    transforms = pe.Node(niu.Merge(2), run_without_submitting=True, name='transforms')

    compare_transforms = pe.Node(niu.Function(function=compare_xforms), name='compare_transforms')

    select_transform = pe.Node(niu.Select(), run_without_submitting=True, name='select_transform')

    fsl_to_lta = pe.MapNode(LTAConvert(out_lta=True), iterfield=['in_fsl'], name='fsl_to_lta')
    # fmt:off
    workflow.connect([
        (flt_bbr, transforms, [('out_matrix_file', 'in1')]),
        (lta_to_fsl, transforms, [('out_fsl', 'in2')]),
        # Convert FSL transforms to LTA (RAS2RAS) transforms and compare
        (inputnode, fsl_to_lta, [('in_file', 'source_file')]),
        (mask_anat_brain, fsl_to_lta, [('out_file', 'target_file')]),
        (transforms, fsl_to_lta, [('out', 'in_fsl')]),
        (fsl_to_lta, compare_transforms, [('out_lta', 'lta_list')]),
        (compare_transforms, outputnode, [('out', 'fallback')]),
        # Select output transform
        (transforms, select_transform, [('out', 'inlist')]),
        (compare_transforms, select_transform, [('out', 'index')]),
        (select_transform, invt_bbr, [('out', 'in_file')]),
        (select_transform, fsl2itk_fwd, [('out', 'transform_file')]),
    ])
    # fmt:on

    return workflow


def compare_xforms(lta_list, norm_threshold=15):
    """
    Computes a normalized displacement between two affine transforms as the
    maximum overall displacement of the midpoints of the faces of a cube, when
    each transform is applied to the cube.
    This combines displacement resulting from scaling, translation and rotation.

    Although the norm is in mm, in a scaling context, it is not necessarily
    equivalent to that distance in translation.

    We choose a default threshold of 15mm as a rough heuristic.
    Normalized displacement above 20mm showed clear signs of distortion, while
    "good" BBR refinements were frequently below 10mm displaced from the rigid
    transform.
    The 10-20mm range was more ambiguous, and 15mm chosen as a compromise.
    This is open to revisiting in either direction.

    See discussion in
    `GitHub issue #681`_ <https://github.com/nipreps/fmriprep/issues/681>`_
    and the `underlying implementation
    <https://github.com/nipy/nipype/blob/56b7c81eedeeae884ba47c80096a5f66bd9f8116/nipype/algorithms/rapidart.py#L108-L159>`_.

    Parameters
    ----------

      lta_list : :obj:`list` or :obj:`tuple` of :obj:`str`
          the two given affines in LTA format
      norm_threshold : :obj:`float`
          the upper bound limit to the normalized displacement caused by the
          second transform relative to the first (default: `15`)

    """
    import nitransforms as nt
    from nipype.algorithms.rapidart import _calc_norm_affine

    bbr_affine = nt.linear.load(lta_list[0]).matrix
    fallback_affine = nt.linear.load(lta_list[1]).matrix

    norm, _ = _calc_norm_affine([fallback_affine, bbr_affine], use_differences=True)

    return norm[1] > norm_threshold


def _conditional_downsampling(in_file, in_mask, zoom_th=4.0):
    """Downsamples the input dataset for sloppy mode."""
    from pathlib import Path

    import nibabel as nb
    import nitransforms as nt
    import numpy as np
    from scipy.ndimage.filters import gaussian_filter

    img = nb.load(in_file)

    zooms = np.array(img.header.get_zooms()[:3])
    if not np.any(zooms < zoom_th):
        return in_file, in_mask

    out_file = Path('desc-resampled_input.nii.gz').absolute()
    out_mask = Path('desc-resampled_mask.nii.gz').absolute()

    shape = np.array(img.shape[:3])
    scaling = zoom_th / zooms
    newrot = np.diag(scaling).dot(img.affine[:3, :3])
    newshape = np.ceil(shape / scaling).astype(int)
    old_center = img.affine.dot(np.hstack((0.5 * (shape - 1), 1.0)))[:3]
    offset = old_center - newrot.dot((newshape - 1) * 0.5)
    newaffine = nb.affines.from_matvec(newrot, offset)

    identity = nt.Affine()

    newref = nb.Nifti1Image(np.zeros(newshape, dtype=np.uint8), newaffine)
    nt.apply(identity, img, reference=newref).to_filename(out_file)

    mask = nb.load(in_mask)
    mask.set_data_dtype(float)
    mdata = gaussian_filter(mask.get_fdata(dtype=float), scaling)
    floatmask = nb.Nifti1Image(mdata, mask.affine, mask.header)
    newmask = nt.apply(identity, floatmask, reference=newref)
    hdr = newmask.header.copy()
    hdr.set_data_dtype(np.uint8)
    newmaskdata = (newmask.get_fdata(dtype=float) > 0.5).astype(np.uint8)
    nb.Nifti1Image(newmaskdata, newmask.affine, hdr).to_filename(out_mask)

    return str(out_file), str(out_mask)
