import thermography as tg
from thermography.io import *
from thermography.detection import *

import cv2
import numpy as np
import os

if __name__ == '__main__':

    # Data input parameters.
    THERMOGRAPHY_ROOT_DIR = tg.settings.get_thermography_root_dir()
    tg.settings.set_data_dir("Z:/SE/SEI/Servizi Civili/Del Don Carlo/termografia/")
    IN_FILE_NAME = os.path.join(tg.settings.get_data_dir(), "Ispez Termografica Ghidoni 1.mov")

    # Input and preprocessing.
    scale_factor = 1.0
    video_loader = VideoLoader(video_path=IN_FILE_NAME, start_frame=500, end_frame=1300, scale_factor=scale_factor)
    # video_loader.show_video(fps=25)

    for i, frame in enumerate(video_loader.frames):
        # frame = cv2.imread("C:/Users/Carlo/Desktop/vertical.jpg")
        gray = cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2GRAY)

        gray = tg.utils.scale_image(gray, scale_factor)
        gray = cv2.blur(gray, (3, 3))

        # Edge detection.
        edge_detector_params = EdgeDetectorParams()
        edge_detector_params.dilation_steps = 2
        edge_detector_params.hysteresis_min_thresh = 30
        edge_detector_params.hysteresis_max_thresh = 100
        edge_detector = EdgeDetector(input_image=gray, params=edge_detector_params)
        edge_detector.detect()

        # Segment detection.
        segment_detector_params = SegmentDetectorParams()
        segment_detector_params.min_line_length = 150
        segment_detector_params.min_num_votes = 100
        segment_detector_params.max_line_gap = 250
        segment_detector = SegmentDetector(input_image=edge_detector.edge_image, params=segment_detector_params)
        segment_detector.detect()

        # Segment clustering.
        segment_clusterer = SegmentClusterer(input_segments=segment_detector.segments)
        segment_clusterer.cluster_segments(num_clusters=2, n_init=8, cluster_type="gmm", swipe_clusters=False)
        # segment_clusterer.plot_segment_features()
        mean_angles, mean_centers = segment_clusterer.compute_cluster_mean()

        unfiltered_segments = segment_clusterer.cluster_list.copy()

        segment_clusterer.clean_clusters(mean_angles=mean_angles, max_angle_variation_mean=np.pi / 180 * 90,
                                         min_intra_distance=20)

        filtered_segments = segment_clusterer.cluster_list.copy()

        # Intersection detection
        intersection_detector = IntersectionDetector(input_segments=filtered_segments)
        intersection_detector.detect()

        # Displaying.
        edges = frame.copy()
        edges_cleaned = frame.copy()

        # Fix colors for first two clusters, choose the next randomly.
        colors = [(0, 255, 255), (255, 255, 0)]
        for cluster_number in range(2, len(unfiltered_segments)):
            colors.append(tg.utils.random_color())

        for cluster, color in zip(unfiltered_segments, colors):
            for segment in cluster:
                cv2.line(img=edges, pt1=(segment[0], segment[1]), pt2=(segment[2], segment[3]),
                         color=color, thickness=1, lineType=cv2.LINE_AA)

        for intersection in intersection_detector.raw_intersections:
            cv2.circle(edges_cleaned, (int(intersection[0]), int(intersection[1])), 3, (0, 0, 255), 1, cv2.LINE_AA)

        cv2.imshow("Skeleton", edge_detector.edge_image)
        cv2.imshow("Segments on input image", edges)
        cv2.imshow("Filtered segments on input image", edges_cleaned)
        cv2.waitKey(1)
