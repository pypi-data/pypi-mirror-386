// hcm/chapter15/tests.rs
use super::*;
use crate::utils::math;
use std::fs::{self, File};
use std::io::BufReader;

fn read_test_files() -> Vec<String> {
    let examples_root_dir: &str = "src/ExampleCases/hcm/TwoLaneHighways/";
    let paths = fs::read_dir(examples_root_dir).expect("Unable to read directory");
    let mut setting_files: Vec<String> = Vec::new();

    for path in paths {
        setting_files.push(path.unwrap().path().display().to_string());
    }

    setting_files.sort();

    setting_files
}

// fn settings<T: SegmentOperations>(setting_file_loc: String) -> TwoLaneHighways<T> {
fn settings(setting_file_loc: String) -> TwoLaneHighways {
    let f = File::open(setting_file_loc).expect("Unable to open file");
    let reader = BufReader::new(f);

    // let twolanehighways: TwoLaneHighways<T> = serde_json::from_reader(reader).expect("Failed to parse JSON");
    let twolanehighways: TwoLaneHighways =
        serde_json::from_reader(reader).expect("Failed to parse JSON");

    twolanehighways
}

// fn case_initialize<T: SegmentOperations>(tlh: TwoLaneHighways<T>) -> (TwoLaneHighways<Segment>, usize) {
fn initialize_test_case(tlh: TwoLaneHighways) -> (TwoLaneHighways, usize) {
    let seg_len = tlh.segments.len();
    let mut segments_vec = Vec::new();

    for seg_num in 0..seg_len {
        // let subseg_len = tlh.segments[seg_num].subsegments.len();
        let subseg_len = tlh.segments[seg_num].get_subsegments().len();
        let mut subsegments_vec = Vec::new();
        for subseg_num in 0..subseg_len {
            let subsegment = SubSegment::new(
                tlh.segments[seg_num].get_subsegments()[subseg_num].length,
                tlh.segments[seg_num].get_subsegments()[subseg_num].avg_speed,
                tlh.segments[seg_num].get_subsegments()[subseg_num].hor_class,
                tlh.segments[seg_num].get_subsegments()[subseg_num].design_rad,
                tlh.segments[seg_num].get_subsegments()[subseg_num].central_angle,
                tlh.segments[seg_num].get_subsegments()[subseg_num].sup_ele,
            );
            subsegments_vec.push(subsegment);
        }

        let segment = Segment::new(
            tlh.segments[seg_num].get_passing_type(),
            tlh.segments[seg_num].get_length(),
            tlh.segments[seg_num].get_grade(),
            tlh.segments[seg_num].get_spl(),
            Some(tlh.segments[seg_num].get_is_hc()),
            Some(tlh.segments[seg_num].get_volume()),
            Some(tlh.segments[seg_num].get_volume_op()),
            Some(tlh.segments[seg_num].get_flow_rate()),
            Some(tlh.segments[seg_num].get_flow_rate_o()),
            Some(tlh.segments[seg_num].get_capacity()),
            Some(tlh.segments[seg_num].get_ffs()),
            Some(tlh.segments[seg_num].get_avg_speed()),
            Some(tlh.segments[seg_num].get_vertical_class()),
            Some(subsegments_vec),
            Some(tlh.segments[seg_num].get_phf()),
            Some(tlh.segments[seg_num].get_phv()),
            Some(tlh.segments[seg_num].get_percent_followers()),
            Some(tlh.segments[seg_num].get_followers_density()),
            Some(tlh.segments[seg_num].get_followers_density_mid()),
            Some(tlh.segments[seg_num].get_hor_class()),
        );
        segments_vec.push(segment);
    }

    let twolanehighways = TwoLaneHighways {
        segments: segments_vec,
        lane_width: tlh.lane_width,
        shoulder_width: tlh.shoulder_width,
        apd: tlh.apd,
        pmhvfl: tlh.pmhvfl,
        l_de: tlh.l_de,
    };

    (twolanehighways, seg_len)
}

#[test]
fn identity_vertical_class_test() {
    let ans_min = vec![
        [0.25, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.25, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.25, 0.5, 0.25, 0.25, 0.25, 0.0],
        [0.5, 0.5, 0.5, 0.5, 0.5, 0.25],
    ];
    let ans_max = vec![
        [3.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [3.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [3.0, 3.0, 3.0, 2.0, 3.0, 0.0],
        [3.0, 3.0, 3.0, 3.0, 3.0, 3.0],
    ];
    let setting_files = read_test_files();

    for (index, s_file) in setting_files.iter().enumerate() {
        // let tlh: TwoLaneHighways<Segment> = settings(s_file.clone());
        let tlh: TwoLaneHighways = settings(s_file.clone());
        let (mut twolanehighways, seg_len) = initialize_test_case(tlh);

        for seg_num in 0..seg_len {
            let (_min, _max) = twolanehighways.identify_vertical_class(seg_num);
            assert_eq!(
                (ans_min[index][seg_num], ans_max[index][seg_num]),
                (_min, _max)
            );
        }
    }
}

#[test]
fn determine_demand_flow_test() {
    let ans_demand_flow_i = vec![
        [800.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [800.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [904.0, 868.0, 863.0, 851.0, 850.0, 0.0],
        [1222.0, 1222.0, 1222.0, 1222.0, 1222.0, 1222.0],
    ];
    let ans_demand_flow_o = vec![
        [1500.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1500.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1500.0, 0.0, 1500.0, 532.0, 1500.0, 0.0],
        [1500.0, 1500.0, 1500.0, 1500.0, 0.0, 1500.0],
    ];
    let ans_capacity = vec![
        [1700.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1700.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1700.0, 1500.0, 1700.0, 1700.0, 1700.0, 0.0],
        [1700.0, 1700.0, 1700.0, 1700.0, 1500.0, 1700.0],
    ];

    let setting_files = read_test_files();
    for (index, s_file) in setting_files.iter().enumerate() {
        // let tlh: TwoLaneHighways<Segment> = settings(s_file.clone());
        let tlh: TwoLaneHighways = settings(s_file.clone());

        let (mut twolanehighways, seg_len) = initialize_test_case(tlh);

        for seg_num in 0..seg_len {
            let (demand_flow_i, demand_flow_o, capacity) =
                twolanehighways.determine_demand_flow(seg_num);
            assert_eq!(
                (
                    ans_demand_flow_i[index][seg_num],
                    ans_demand_flow_o[index][seg_num],
                    ans_capacity[index][seg_num]
                ),
                // (demand_flow_i, math::round_to_significant_digits(demand_flow_o, 3), capacity.into()));
                (
                    demand_flow_i.round(),
                    demand_flow_o.round(),
                    capacity.into()
                )
            );
        }
    }
}

#[test]
fn determine_vertical_alignment_test() {
    let ans_ver_align = vec![
        [1, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1],
        [4, 5, 4, 4, 1, 1],
    ];

    let setting_files = read_test_files();
    for (index, s_file) in setting_files.iter().enumerate() {
        // let tlh : TwoLaneHighways<Segment>= settings(s_file.clone());
        let tlh: TwoLaneHighways = settings(s_file.clone());
        let (mut twolanehighways, seg_len) = initialize_test_case(tlh);

        for seg_num in 0..seg_len {
            let ver_align = twolanehighways.determine_vertical_alignment(seg_num);
            assert_eq!(ans_ver_align[index][seg_num], ver_align);
        }
    }
}

#[test]
fn determine_free_flow_speed_test() {
    let ans_ffs = vec![
        [56.83, 0.0, 0.0, 0.0, 0.0, 0.0],
        [56.83, 0.0, 0.0, 0.0, 0.0, 0.0],
        [62.43, 62.43, 62.43, 62.45, 62.43, 0.0],
        [60.02, 59.04, 60.07, 60.02, 62.43, 62.43],
    ];
    let setting_files = read_test_files();

    for (index, s_file) in setting_files.iter().enumerate() {
        // let tlh : TwoLaneHighways<Segment>= settings(s_file.clone());
        let tlh: TwoLaneHighways = settings(s_file.clone());

        let (mut twolanehighways, seg_len) = initialize_test_case(tlh);

        for seg_num in 0..seg_len {
            let (_, _, _) = twolanehighways.determine_demand_flow(seg_num);
            let ffs = twolanehighways.determine_free_flow_speed(seg_num);
            assert_eq!(ans_ffs[index][seg_num], math::round_up_to_n_decimal(ffs, 2));
        }
    }
}

#[test]
fn estimate_average_speed_test() {
    let ans_s = vec![
        [53.7, 0.0, 0.0, 0.0, 0.0, 0.0],
        [49.5, 0.0, 0.0, 0.0, 0.0, 0.0],
        [58.8, 57.8, 58.9, 59.2, 58.9, 0.0],
        [47.9, 43.9, 50.8, 49.2, 56.0, 58.3],
    ];
    let setting_files = read_test_files();
    for (index, s_file) in setting_files.iter().enumerate() {
        // let tlh : TwoLaneHighways<Segment>= settings(s_file.clone());
        let tlh: TwoLaneHighways = settings(s_file.clone());

        let (mut twolanehighways, seg_len) = initialize_test_case(tlh);

        // Set free flow speed
        for seg_num in 0..seg_len {
            let (_, _, _) = twolanehighways.determine_demand_flow(seg_num);
            let _ = twolanehighways.determine_free_flow_speed(seg_num);
            let (s, _) = twolanehighways.estimate_average_speed(seg_num);

            // let subseg_num = twolanehighways.get_segments()[seg_num].get_subsegments().len();
            // while j < subseg_num {
            //     tot_s += s;
            // }
            assert_eq!(ans_s[index][seg_num], math::round_up_to_n_decimal(s, 1));
        }
    }
}

#[test]
fn estimate_percent_followers_test() {
    let ans_pf = vec![
        [67.7, 0.0, 0.0, 0.0, 0.0, 0.0],
        [67.7, 0.0, 0.0, 0.0, 0.0, 0.0],
        [69.7, 60.7, 68.0, 67.8, 67.7, 0.0],
        [86.9, 89.3, 83.9, 86.9, 78.2, 78.4],
    ];
    let setting_files = read_test_files();
    for (index, s_file) in setting_files.iter().enumerate() {
        // let tlh : TwoLaneHighways<Segment>= settings(s_file.clone());
        let tlh: TwoLaneHighways = settings(s_file.clone());
        let (mut twolanehighways, seg_len) = initialize_test_case(tlh);

        for seg_num in 0..seg_len {
            let (_, _, _) = twolanehighways.determine_demand_flow(seg_num);
            let _ = twolanehighways.determine_free_flow_speed(seg_num);
            let pf = twolanehighways.estimate_percent_followers(seg_num);
            assert_eq!(
                ans_pf[index][seg_num],
                math::round_to_significant_digits(pf, 3)
            );
        }
    }
}

#[test]
fn determine_follower_density_test() {
    // let ans_fd = vec![[10.1, 0.0, 0.0, 0.0, 0.0, 0.0], [10.9, 0.0, 0.0, 0.0, 0.0, 0.0], [10.7, 9.1, 10.0, 9.8, 9.8, 0.0], [22.2, 24.9, 20.2, 21.6, 17.2, 16.4]];
    let ans_fd = vec![
        [10.1, 0.0, 0.0, 0.0, 0.0, 0.0],
        [10.9, 0.0, 0.0, 0.0, 0.0, 0.0],
        [10.7, 9.1, 10.0, 9.7, 9.8, 0.0],
        [22.2, 24.9, 20.2, 21.6, 17.1, 16.4],
    ];
    let setting_files = read_test_files();
    for (index, s_file) in setting_files.iter().enumerate() {
        // let tlh : TwoLaneHighways<Segment>= settings(s_file.clone());
        let tlh: TwoLaneHighways = settings(s_file.clone());

        let (mut twolanehighways, seg_len) = initialize_test_case(tlh);

        let mut fd: f64;

        for seg_num in 0..seg_len {
            let (_, _, _) = twolanehighways.determine_demand_flow(seg_num);
            let _ = twolanehighways.determine_free_flow_speed(seg_num);
            let (_, _) = twolanehighways.estimate_average_speed(seg_num);
            let _ = twolanehighways.estimate_percent_followers(seg_num);
            if twolanehighways.get_segments()[seg_num].passing_type == 2 {
                (fd, _) = twolanehighways.determine_follower_density_pl(seg_num);
            } else {
                fd = twolanehighways.determine_follower_density_pc_pz(seg_num);
            }

            assert_eq!(ans_fd[index][seg_num], math::round_up_to_n_decimal(fd, 1));
        }
    }
}

#[test]
fn determine_adjustment_to_follower_density_test() {
    let ans_fd_adj = vec![
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 10.3, 8.3, 8.2, 8.8, 0.0],
        [0.0, 0.0, 0.0, 0.0, 18.0, 13.2],
    ];
    let setting_files = read_test_files();
    for (index, s_file) in setting_files.iter().enumerate() {
        // let tlh : TwoLaneHighways<Segment>= settings(s_file.clone());
        let tlh: TwoLaneHighways = settings(s_file.clone());

        let (mut twolanehighways, seg_len) = initialize_test_case(tlh);

        for seg_num in 0..seg_len {
            println!("Case {}", index);
            println!("Segment {}", seg_num);
            let (_, _, _) = twolanehighways.determine_demand_flow(seg_num);
            let _ = twolanehighways.determine_free_flow_speed(seg_num);
            let (_, _) = twolanehighways.estimate_average_speed(seg_num);
            let _ = twolanehighways.estimate_percent_followers(seg_num);
            let _ = twolanehighways.determine_follower_density_pc_pz(seg_num);

            let fd_adj = twolanehighways.determine_adjustment_to_follower_density(seg_num);

            // assert_eq!(ans_fd_adj[index][seg_num], math::round_to_significant_digits(fd_adj, 3));
            assert_eq!(
                ans_fd_adj[index][seg_num],
                math::round_up_to_n_decimal(fd_adj, 1)
            );
        }
    }
}

#[test]
fn determine_segment_los_test() {
    let ans_los = vec![
        ['D', '\0', '\0', '\0', '\0', '\0'],
        ['D', '\0', '\0', '\0', '\0', '\0'],
        ['D', 'B', 'D', 'D', 'D', '\0'],
        ['E', 'E', 'E', 'E', 'C', 'E'],
    ];
    let setting_files = read_test_files();
    for (index, s_file) in setting_files.iter().enumerate() {
        // let tlh : TwoLaneHighways<Segment>= settings(s_file.clone());
        let tlh: TwoLaneHighways = settings(s_file.clone());

        let (mut twolanehighways, seg_len) = initialize_test_case(tlh);

        for seg_num in 0..seg_len {
            let (_, _, capacity) = twolanehighways.determine_demand_flow(seg_num);
            let _ = twolanehighways.determine_free_flow_speed(seg_num);
            let (s, _) = twolanehighways.estimate_average_speed(seg_num);
            let _ = twolanehighways.estimate_percent_followers(seg_num);
            if twolanehighways.get_segments()[seg_num].get_passing_type() == 2 {
                let (_, _) = twolanehighways.determine_follower_density_pl(seg_num);
            } else {
                let _ = twolanehighways.determine_follower_density_pc_pz(seg_num);
            }
            let los = twolanehighways.determine_segment_los(seg_num, s, capacity);

            assert_eq!(ans_los[index][seg_num], los);
        }
    }
}

#[test]
fn determine_facility_los_test() {
    let ans_los = vec!['D', 'D', 'D', 'E'];

    let setting_files = read_test_files();
    for (index, s_file) in setting_files.iter().enumerate() {
        // let tlh : TwoLaneHighways<Segment>= settings(s_file.clone());
        let tlh: TwoLaneHighways = settings(s_file.clone());

        let (mut twolanehighways, seg_len) = initialize_test_case(tlh);
        let mut tot_len: f64 = 0.0;
        let mut fd_f: f64 = 0.0;
        let mut s_tot: f64 = 0.0;
        let mut fd: f64;
        let mut fd_mid: f64;

        for seg_num in 0..seg_len {
            let (_, _, _) = twolanehighways.determine_demand_flow(seg_num);
            let _ = twolanehighways.determine_free_flow_speed(seg_num);
            let (s, _) = twolanehighways.estimate_average_speed(seg_num);
            let _ = twolanehighways.estimate_percent_followers(seg_num);
            if twolanehighways.get_segments()[seg_num].get_passing_type() == 2 {
                (_, fd_mid) = twolanehighways.determine_follower_density_pl(seg_num);
                fd_f += fd_mid * twolanehighways.get_segments()[seg_num].get_length();
            } else {
                fd = twolanehighways.determine_follower_density_pc_pz(seg_num);
                fd_f += fd * twolanehighways.get_segments()[seg_num].get_length();
            }
            tot_len += twolanehighways.get_segments()[seg_num].get_length();
            s_tot += s * twolanehighways.get_segments()[seg_num].get_length();
        }
        fd_f = fd_f / tot_len;

        let average_speed = s_tot / tot_len;
        let fac_los = twolanehighways.determine_facility_los(fd_f, average_speed);

        assert_eq!(ans_los[index], fac_los);
    }
}
