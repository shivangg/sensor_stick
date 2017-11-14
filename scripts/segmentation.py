#!/usr/bin/env python

# Import modules
from pcl_helper import *

# TODO: Define functions as required

# Callback function for your Point Cloud Subscriber
def pcl_callback(pcl_msg):

    ## TODO: Convert ROS msg to PCL data

    cloud = ros_to_pcl(pcl_msg)

    ## TODO: Voxel Grid Downsampling
    vox = cloud.make_voxel_grid_filter()
    LEAF_SIZE = 0.01  
    vox.set_leaf_size(LEAF_SIZE, LEAF_SIZE, LEAF_SIZE)
    cloud_filtered = vox.filter()

    ## TODO: PassThrough Filter

    passthrough = cloud_filtered.make_passthrough_filter() 
    filter_axis = 'z'
    passthrough.set_filter_field_name(filter_axis)
    axis_min = 0.77
    axis_max = 1.2
    passthrough.set_filter_limits(axis_min, axis_max)
    cloud_filtered = passthrough.filter()

    ## TODO: RANSAC Plane Segmentation

    seg = cloud_filtered.make_segmenter()

    # set the model which has to be fit
    seg.set_model_type(pcl.SACMODEL_PLANE)
    seg.set_method_type(pcl.SAC_RANSAC)

    # max distance for the point to be considered fit
    max_distance = 0.01
    seg.set_distance_threshold(max_distance)

    ## TODO: Extract inliers and outliers
    
    inliers, coefficients = seg.segment()
    
    # Extract inliers
    extracted_outliers = cloud_filtered.extract(inliers, negative = True)
    extracted_inliers = cloud_filtered.extract(inliers, negative = False)
    
    # TODO: Euclidean Clustering
    white_cloud = XYZRGB_to_XYZ(extracted_outliers)
    tree = white_cloud.make_kdtree()

    # create a cluster extraction object

    ec = white_cloud.make_EuclideanClusterExtraction()
    # set tolerance for distance threshold
    # as well as max. and min. cluster size(in points)

    ec.set_ClusterTolerance(0.02)
    ec.set_MinClusterSize(6)
    ec.set_MaxClusterSize(250000)

    # search the kd tree for clusters
    ec.set_SearchMethod(tree)
    # extract indices for each of the discovered cluster
    cluster_indices = ec.Extract()
    # TODO: Create Cluster-Mask Point Cloud to visualize each cluster separately

    cluster_color = get_color_list(len(cluster_indices))

    color_cluster_point_list = []

    for j, indices in enumerate(cluster_indices):
        for i, indice in enumerate(indices):
            color_cluster_point_list.append([white_cloud[indice][0],
                                            white_cloud[indice][1],
                                            white_cloud[indice][2],
                                            rgb_to_float(cluster_color[j])
                                        ])

    # create new cloud containing all clusters, each with unique color
    cluster_cloud = pcl.PointCloud_PointXYZRGB()
    cluster_cloud.from_list(color_cluster_point_list)

    # TODO: Convert PCL data to ROS messages
    
    pcl_to_ros_objects = pcl_to_ros(extracted_outliers)
    pcl_to_ros_table = pcl_to_ros(extracted_inliers)
    
    ros_cluster_cloud = pcl_to_ros(cluster_cloud)

    # TODO: Publish ROS messages
    pcl_objects_pub.publish(pcl_to_ros_objects)
    pcl_table_pub.publish(pcl_to_ros_table)

    pcl_cluster_pub.publish(ros_cluster_cloud)


if __name__ == '__main__':

    # TODO: ROS node initialization
    rospy.init_node('clustering', anonymous = True)
    # TODO: Create Subscribers

    rospy.Subscriber('/sensor_stick/point_cloud', pc2.PointCloud2, pcl_callback, queue_size = 2)

    # TODO: Create Publishers
    pcl_objects_pub = rospy.Publisher('/pcl_objects', PointCloud2, queue_size = 1)
    pcl_table_pub = rospy.Publisher('/pcl_table', PointCloud2, queue_size = 1)
    pcl_cluster_pub = rospy.Publisher('/pcl_cluster', PointCloud2, queue_size = 1)

    # Initialize color_list
    get_color_list.color_list = []

    # TODO: Spin while node is not shutdown
    while not rospy.is_shutdown():
        rospy.spin()

