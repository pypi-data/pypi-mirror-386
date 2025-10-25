from pathlib import Path

from dist_s1.workflows import (
    run_burst_disturbance_workflow,
    run_dist_s1_localization_workflow,
    run_dist_s1_packaging_workflow_no_confirmation,
    run_disturbance_merge_workflow,
)


def main() -> None:
    mgrs_tile_id = '11SLT'
    post_date = '2025-01-21'
    track_number = 71
    dst_dir = Path('../../notebooks/los-angeles')
    memory_strategy = 'high'
    low_confidence_alert_threshold = 3.5
    high_confidence_alert_threshold = 5.5

    run_config = run_dist_s1_localization_workflow(
        mgrs_tile_id,
        post_date,
        track_number,
        post_date_buffer_days=1,
        dst_dir=dst_dir,
        input_data_dir=dst_dir,
    )
    run_config.apply_water_mask = True
    run_config.src_water_mask_path = dst_dir / 'water_mask.tif'
    run_config.algo_config.memory_strategy = memory_strategy
    run_config.algo_config.low_confidence_alert_threshold = low_confidence_alert_threshold
    run_config.algo_config.high_confidence_alert_threshold = high_confidence_alert_threshold

    run_burst_disturbance_workflow(run_config)
    run_disturbance_merge_workflow(run_config)
    run_dist_s1_packaging_workflow_no_confirmation(run_config)


if __name__ == '__main__':
    main()
