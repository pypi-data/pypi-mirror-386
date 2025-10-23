"""
Example script for contrast-agnostic registration using SynthSeg

This script demonstrates a full registration pipeline that uses SynthSeg's brain
parcellation to enable registration between images of different contrasts:

1. Generate parcellations of both input and reference images using SynthSeg
2. Register the parcellations to each other (contrast-agnostic)
3. Apply the resulting transformation to the original input image

This approach is useful for registering images with very different contrasts
(e.g., T1w to T2w, FLAIR to T1w, etc.) where direct intensity-based
registration might fail.
"""

import os
import argparse
import subprocess
import sys
import multiprocessing
import tempfile
DEFAULT_THREADS = multiprocessing.cpu_count()

def lamareg(
    input_image,
    reference_image,
    output_image=None,
    input_parc=None,
    reference_parc=None,
    output_parc=None,
    generate_warpfield=False,
    apply_warpfield=False,
    registration_method="SyNRA",
    affine_file=None,
    warp_file=None,
    inverse_warp_file=None,
    synthseg_threads=DEFAULT_THREADS,
    ants_threads=DEFAULT_THREADS,
    qc_csv=None,
    skip_fixed_parc=False,
    skip_moving_parc=False,
    skip_qc=False,
    disable_robust=False,
    inverse=False,
    secondary_warp_file=None,
    inverse_secondary_warp_file=None,
    verbose=False
    
):
    """
    Perform contrast-agnostic registration using SynthSeg parcellation.
    """
    # Validate arguments based on the selected workflow
    if generate_warpfield and apply_warpfield:
        raise ValueError(
            "Cannot use both --generate-warpfield and --apply-warpfield at the same time"
        )

    # Validate input files exist
    for input_file in [f for f in [input_image, reference_image] if f is not None]:
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

    # Validate thread counts
    if synthseg_threads < 1:
        raise ValueError(
            f"Invalid thread count for SynthSeg: {synthseg_threads}. Must be >= 1"
        )
    if ants_threads < 1:
        raise ValueError(f"Invalid thread count for ANTs: {ants_threads}. Must be >= 1")
    print("skip qc = ", skip_qc)
    # Workflow-specific validation
    if not apply_warpfield:
        # Registration or Generate-warpfield workflow
        if input_image is None:
            raise ValueError("--moving is required for registration")
        if reference_image is None:
            raise ValueError("--fixed is required for registration")
        if input_parc is None:
            raise ValueError("--moving-parc is required for registration")
        if reference_parc is None:
            raise ValueError("--fixed-parc is required for registration")
        if output_parc is None:
            raise ValueError("--registered-parc is required for registration")

        # For normal registration (not generate-warpfield), output image is required
        if not generate_warpfield and output_image is None:
            raise ValueError("--output is required for registration")

        # If generating warpfield, warn if transform files not specified
        if affine_file is None:
            print(
                "Warning: No affine transform file path provided - affine transform will not be saved"
            )
        if warp_file is None:
            print(
                "Warning: No warp field file path provided - warp field will not be saved"
            )
        if inverse_warp_file is None:
            print(
                "Warning: No inverse warp field file path provided - inverse warp field will not be saved"
            )
        if secondary_warp_file is None:
            if not disable_robust:
                print(
                    "Warning: No secondary warp field file path provided - first and second stage warp fields will be composed"
                )
                print(
                    "Warning: Warpfield composition can result in loss of precision and accuracy in the resulting warpfields. Consider providing a secondary warp field file path for improved results if you plan to re-use warpfields."
                )
        if inverse_secondary_warp_file is None:
            if not disable_robust:
                print(
                    "Warning: No inverse secondary warp field file path provided - first and second stage inverse warp fields will be composed"
                )
                print(
                    "Warning: Warpfield composition can result in loss of precision and accuracy in the resulting warpfields. Consider providing a secondary inverse warp field file path for improved results if you plan to re-use warpfields."
                )
    else:
        # Apply-warpfield workflow
        if input_image is None:
            raise ValueError("--moving is required for apply-warpfield")
        if reference_image is None:
            raise ValueError("--fixed is required for apply-warpfield")
        if output_image is None:
            raise ValueError("--output is required for apply-warpfield")
        if affine_file is None:
            raise ValueError("--affine is required for apply-warpfield")
        if warp_file is None:
            raise ValueError("--warpfield is required for apply-warpfield")

        # Validate transform files exist
        for transform_file in [affine_file, warp_file]:
            if not os.path.isfile(transform_file):
                raise FileNotFoundError(f"Transform file not found: {transform_file}")

    # Add QC CSV validation
    if not apply_warpfield and not generate_warpfield:
        # Only relevant for standard registration workflow
        if qc_csv is None:
            # No QC CSV path provided, will use default
            if output_parc is not None:
                default_qc_path = os.path.splitext(output_parc)[0] + "_dice_scores.csv"
                print(
                    f"No QC CSV path provided - Dice scores will be saved to: {default_qc_path}"
                )
        else:
            # QC CSV path provided, check if directory is writable
            qc_dir = os.path.dirname(qc_csv)
            if qc_dir:
                if os.path.exists(qc_dir):
                    if not os.access(qc_dir, os.W_OK):
                        raise PermissionError(
                            f"Cannot write to QC CSV directory: {qc_dir}. Check permissions."
                        )
                else:
                    try:
                        os.makedirs(qc_dir, exist_ok=True)
                    except Exception as e:
                        raise PermissionError(
                            f"Cannot create QC CSV directory: {qc_dir}. Error: {e}"
                        )

    # Create directories for all output files
    for file_path in [
        output_image,
        input_parc,
        reference_parc,
        output_parc,
        affine_file,
        warp_file,
        inverse_warp_file,
        qc_csv,
    ]:
        if file_path is not None:
            output_dir = os.path.dirname(file_path)
            if output_dir:  # Only try to create if there's a directory part
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except PermissionError:
                    raise PermissionError(
                        f"Cannot create output directory: {output_dir}. Check permissions."
                    )

    print(f"Processing input image: {input_image}")
    print(f"Reference image: {reference_image}")
    print(
        f"Using {synthseg_threads} thread(s) for SynthSeg and {ants_threads} thread(s) for ANTs"
    )

    # Create environment with suppressed TensorFlow warnings
    env = os.environ.copy()
    env["TF_CPP_MIN_LOG_LEVEL"] = "3"  # 0=ALL, 1=INFO, 2=WARNING, 3=ERROR
    env["PYTHONWARNINGS"] = "ignore"

    # Set ANTs/ITK thread count
    env["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(ants_threads)
    env["OMP_NUM_THREADS"] = str(ants_threads)  # OpenMP threads for ANTs

    temp_files = []
    temp_warp_file = None
    temp_inverse_warp_file = None
    temp_parc_file = None

    try:
        # WORKFLOW 1 & 2: Full registration or generate warpfield
        if not apply_warpfield:
            # Step 1: Generate parcellations with SynthSeg if needed
            if not skip_moving_parc:
                print("\n--- Step 1.1: Generating parcellation for input image ---")
                subprocess.run(
                    [
                        "lamareg",
                        "synthseg",
                        "--i",
                        input_image,
                        "--o",
                        input_parc,
                        "--parc",
                        "--cpu",
                        "--robust",
                        "--threads",
                        str(synthseg_threads),  # Use SynthSeg threads
                    ],
                    check=True,
                    env=env,
                )
            else:
                print(
                    f"Skipping parcellation generation for input image: {input_image}"
                )
                print(f"Using provided parcellation: {input_parc}")
            # Check if the input parcellation file exists
            if not os.path.isfile(input_parc):
                raise FileNotFoundError(
                    f"Input parcellation file not found: {input_parc}"
                )

            if not skip_fixed_parc:
                print("\n--- Step 1.2: Generating parcellation for reference image ---")
                subprocess.run(
                    [
                        "lamareg",
                        "synthseg",
                        "--i",
                        reference_image,
                        "--o",
                        reference_parc,
                        "--parc",
                        "--cpu",
                        "--robust",
                        "--threads",
                        str(synthseg_threads),  # Use SynthSeg threads
                    ],
                    check=True,
                    env=env,
                )
            else:
                print(
                    f"Skipping parcellation generation for reference image: {reference_image}"
                )
                print(f"Using provided parcellation: {reference_parc}")
            # Check if the reference parcellation file exists
            if not os.path.isfile(reference_parc):
                raise FileNotFoundError(
                    f"Reference parcellation file not found: {reference_parc}"
                )

            # Step 2: Register parcellations using coregister
            print("\n--- Step 2: Coregistering parcellated images ---")
            cmd = [
                "lamareg",
                "coregister",
                "--fixed",
                reference_parc,
                "--moving",
                input_parc,
                "--registration-method",
                registration_method,
                "--fixed-image",
                reference_image,
            ]

            if output_parc is not None:
                if not disable_robust:
                    with tempfile.NamedTemporaryFile(suffix="_tmp_output_parc.nii.gz", delete=False) as tmp_parc:
                        temp_parc_file = tmp_parc.name
                    temp_files.append(temp_parc_file)
                    cmd.extend(["--output", temp_parc_file])
                else:
                    cmd.extend(["--output", output_parc])


            # Only include transform file flags if paths were provided
            if affine_file:
                cmd.extend(["--affine-file", affine_file])

            if warp_file:
                if not disable_robust:
                    if not secondary_warp_file:
                        with tempfile.NamedTemporaryFile(suffix="_tmp_warp.nii.gz", delete=False) as tmp_warp:
                            temp_warp_file = tmp_warp.name
                        temp_files.append(temp_warp_file)
                        cmd.extend(["--warp-file", temp_warp_file])
                    else:
                        cmd.extend(["--warp-file", warp_file])
                else:
                    cmd.extend(["--warp-file", warp_file])

            if inverse_warp_file:
                if not disable_robust:
                    if not inverse_secondary_warp_file:
                        with tempfile.NamedTemporaryFile(suffix="_tmp_inverse_warp.nii.gz", delete=False) as tmp_inverse_warp:
                            temp_inverse_warp_file = tmp_inverse_warp.name
                        temp_files.append(temp_inverse_warp_file)
                        cmd.extend(["--inverse-warp-file", temp_inverse_warp_file])
                    else:
                        cmd.extend(["--inverse-warp-file", inverse_warp_file])
                else:
                    cmd.extend(["--inverse-warp-file", inverse_warp_file])

            if verbose:
                cmd.append("--verbose")
            subprocess.run(cmd, check=True, env=env)
            if not disable_robust:
                print(
                    "\n--- Step 2.1: Running robust registration for improved accuracy ---"
                )
                robust_cmd = [
                    "lamareg",
                    "coregister",
                    "--fixed",
                    reference_image,
                    "--moving",
                    input_image,
                    "--interpolator",
                    "linear",
                    "--registration-method",
                    "SyNOnly",
                    "--initial-affine-file",
                    affine_file,
                    "--initial-warp-file",
                    temp_warp_file if not secondary_warp_file else warp_file,
                    "--reg-iterations",
                    "10, 20",
                ]
                if inverse_warp_file or not skip_qc:
                    if not inverse_secondary_warp_file:
                        robust_cmd.extend(["--initial-inverse-warp-file", temp_inverse_warp_file])
                    else:
                        robust_cmd.extend(["--initial-inverse-warp-file", inverse_warp_file])
                if output_image is not None:
                    robust_cmd.extend(["--output", output_image])

                # Only include transform file flags if paths were provided
                if affine_file or not skip_qc:
                    robust_cmd.extend(["--affine-file", affine_file])

                if warp_file or not skip_qc:
                    if secondary_warp_file:
                        robust_cmd.extend(["--warp-file", secondary_warp_file])
                        robust_cmd.extend(["--disable-warp-composition"])
                    else:
                        robust_cmd.extend(["--warp-file", warp_file])

                if inverse_warp_file:
                    if inverse_secondary_warp_file:
                        robust_cmd.extend(["--inverse-warp-file", inverse_secondary_warp_file])
                        robust_cmd.extend(["--disable-inverse-warp-composition"])
                    else:
                        robust_cmd.extend(["--inverse-warp-file", inverse_warp_file])
                if verbose:
                    robust_cmd.append("--verbose")
                subprocess.run(robust_cmd, check=True, env=env)
                try:
                    if temp_warp_file and os.path.exists(temp_warp_file):
                        os.remove(temp_warp_file)
                    if temp_inverse_warp_file and os.path.exists(temp_inverse_warp_file):
                        os.remove(temp_inverse_warp_file)
                except OSError:
                    pass

                apply_cmd = [
                    "lamareg",
                    "apply-warp",  # Use hyphen instead of underscore
                    "--moving",
                    input_parc,
                    "--fixed",  # Changed from --reference to --fixed
                    reference_image,
                    "--output",
                    output_parc, 
                    "--interpolation",
                    "nearestNeighbor",
                ]
                
                # Only include transform file flags if files were provided
                apply_cmd.extend(["--affine", affine_file])
                    
                apply_cmd.extend(["--warp", warp_file])

                if secondary_warp_file:
                    apply_cmd.extend(["--secondary-warp", secondary_warp_file])
                if verbose:
                    apply_cmd.append("--verbose")
                subprocess.run(apply_cmd, check=True, env=env)
                    
            # Run Dice evaluation after coregistration
            if not skip_qc:


                # If qc_csv is not provided, generate a default path based on output_parc
                dice_output = (
                    qc_csv
                    if qc_csv
                    else output_parc.split('.')[0] + "_dice_scores.csv"
                )

                print(
                    "\n--- Step 3: Calculating Dice scores to evaluate registration quality ---"
                )
                try:
                    from lamareg.scripts.dice_compare import compare_parcellations_dice

                    compare_parcellations_dice(reference_parc, output_parc, dice_output, verbose=verbose)
                    print(f"Quality control metrics saved to: {dice_output}")
                except FileNotFoundError as e:
                    print(
                        f"Warning: Could not calculate Dice scores - file not found: {e}",
                        file=sys.stderr,
                    )
                except PermissionError as e:
                    print(
                        f"Warning: Could not calculate Dice scores - permission error: {e}",
                        file=sys.stderr,
                    )
                except ImportError as e:
                    print(
                        f"Warning: Could not calculate Dice scores - dice_compare module not found",
                        file=sys.stderr,
                    )
                except Exception as e:
                    print(
                        f"Warning: Could not calculate Dice scores: {e}",
                        file=sys.stderr,
                    )

        # WORKFLOW 1 & 3: Apply transformation to the original input image
        if not generate_warpfield and output_image is not None and (disable_robust or apply_warpfield):
            print(
                "\n--- Step 4: Applying transformation to original input image ---"
            )
            apply_cmd = [
                "lamareg",
                "apply-warp",  # Use hyphen instead of underscore
                "--moving",
                input_image,
                "--fixed",  # Changed from --reference to --fixed
                reference_image,
                "--output",
                output_image, 
            ]

            # Only include transform file flags if files were provided
            if affine_file:
                apply_cmd.extend(["--affine", affine_file])

            if warp_file:
                apply_cmd.extend(["--warp", warp_file])
            
            if secondary_warp_file:
                apply_cmd.extend(["--secondary-warp", secondary_warp_file])

            if inverse:
                apply_cmd.extend(["--inverse"])
            if verbose:
                apply_cmd.append("--verbose")
            subprocess.run(apply_cmd, check=True, env=env)

            print(f"\nSuccess! Registered image saved to: {output_image}")
        elif generate_warpfield:
            success_msg = "\nSuccess! "
            if warp_file:
                success_msg += f"Warp field generated at: {warp_file}"
            if affine_file:
                success_msg += f"\nAffine transformation saved at: {affine_file}"
            print(success_msg)

    except subprocess.CalledProcessError as e:
        print(f"Error during processing: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        for temp_path in temp_files:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


def main():
    """Entry point for command-line use"""
    parser = argparse.ArgumentParser(
        description="Contrast-agnostic registration using SynthSeg"
    )
    parser.add_argument(
        "--moving", required=True, help="Input moving image to be registered"
    )
    parser.add_argument(
        "--fixed", required=True, help="Reference fixed image (target space)"
    )
    parser.add_argument(
        "--skip-fixed-parc",
        action="store_true",
        help="Skip generating fixed parcellation",
    )
    parser.add_argument(
        "--skip-moving-parc",
        action="store_true",
        help="Skip generating moving parcellation",
    )
    parser.add_argument("--output", help="Output registered image")
    parser.add_argument(
        "--moving-parc", required=True, help="Path for moving image parcellation"
    )
    parser.add_argument(
        "--fixed-parc", required=True, help="Path for fixed image parcellation"
    )
    parser.add_argument(
        "--registered-parc", required=True, help="Path for registered parcellation"
    )
    parser.add_argument(
        "--affine", required=True, help="Path for affine transformation"
    )
    parser.add_argument("--warpfield", required=True, help="Path for warp field")
    parser.add_argument("--inverse-warpfield", help="Path for inverse warp field")
    parser.add_argument(
        "--generate-warpfield",
        action="store_true",
        help="Generate warp field without applying it",
    )
    parser.add_argument(
        "--apply-warpfield",
        action="store_true",
        help="Apply existing warp field to moving image",
    )
    parser.add_argument(
        "--registration-method", default="SyNRA", help="Registration method"
    )
    parser.add_argument(
        "--synthseg-threads",
        type=int,
        default=DEFAULT_THREADS,
        help="Number of threads to use for SynthSeg segmentation",
    )
    parser.add_argument(
        "--ants-threads",
        type=int,
        default=DEFAULT_THREADS,
        help="Number of threads to use for ANTs registration",
    )
    parser.add_argument("--secondary-warpfield", help="Path for secondary warp field (for robust registration)")
    parser.add_argument("--inverse-secondary-warpfield", help="Path for inverse of secondary warp field (for robust registration)")
    parser.add_argument("--qc-csv", help="Path for quality control Dice score CSV file")
    parser.add_argument("--skip-qc", action="store_true", help="Skip QC CSV generation")
    parser.add_argument("--disable-robust", action="store_true", help="Disable robust second-stage registration")
    parser.add_argument("--inverse", action="store_true", help="Whether to reverse the order of the transforms (warpfield first, then affine)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # Validate arguments based on workflow
    if args.apply_warpfield and (args.affine is None or args.warpfield is None):
        parser.error("--apply-warpfield requires --affine and --warpfield arguments")

    if args.generate_warpfield and args.output is not None:
        parser.error(
            "--generate-warpfield cannot be used with --output (no output image is produced)"
        )

    if not args.apply_warpfield and not args.generate_warpfield and args.output is None:
        parser.error(
            "--output is required unless --generate-warpfield or --apply-warpfield is specified"
        )

    lamareg(
        input_image=args.moving,
        reference_image=args.fixed,
        output_image=args.output,
        input_parc=args.moving_parc,
        reference_parc=args.fixed_parc,
        output_parc=args.registered_parc,
        generate_warpfield=args.generate_warpfield,
        apply_warpfield=args.apply_warpfield,
        registration_method=args.registration_method,
        affine_file=args.affine,
        warp_file=args.warpfield,
        inverse_warp_file=args.inverse_warpfield,
        synthseg_threads=args.synthseg_threads,
        ants_threads=args.ants_threads,
        qc_csv=args.qc_csv,
        skip_fixed_parc=args.skip_fixed_parc,
        skip_moving_parc=args.skip_moving_parc,
        skip_qc=args.skip_qc,
        disable_robust=args.disable_robust,
        inverse=args.inverse,
        secondary_warp_file=args.secondary_warpfield,
        inverse_secondary_warp_file=args.inverse_secondary_warpfield,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
