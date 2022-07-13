_base_ = [
    '../../../../_base_/default_runtime.py',
    '../../../../_base_/datasets/crowdpose.py'
]
checkpoint_config = dict(interval=50)
evaluation = dict(interval=50, metric='mAP', save_best='AP')

optimizer = dict(
    type='Adam',
    lr=0.008,
)
optimizer_config = dict(grad_clip=None)
# learning policy
lr_config = dict(
    policy='CosineAnnealing',
    warmup='linear',
    warmup_iters=500,
    warmup_ratio=0.001,
    min_lr=0.00001)
total_epochs = 500
channel_cfg = dict(
    dataset_joints=14,
    dataset_channel=[
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
    ],
    inference_channel=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])

data_cfg = dict(
    image_size=256,
    base_size=256,
    base_sigma=2,
    heatmap_size=[64, 128],
    num_joints=channel_cfg['dataset_joints'],
    dataset_channel=channel_cfg['dataset_channel'],
    inference_channel=channel_cfg['inference_channel'],
    num_scales=2,
    scale_aware_sigma=False)

model = dict(
    type='AssociativeEmbedding',
    # TODO: unify pretrained model path
    pretrained='/home/junyan/litepose-model-zoo'
    '/crowd/crowdpose-XS-pretrain-epoch826-0628-mmpose.pth',
    backbone=dict(
        type='LitePose',
        input_channel=16,
        num_blocks=(6, 8, 10, 10),
        strides=(2, 2, 2, 1),
        channels=(16, 32, 48, 80),
        block_settings=([[6, 7]] * 6, [[6, 7]] * 8, [[6, 7]] * 10,
                        [[6, 7]] * 10)),
    keypoint_head=dict(
        type='LitePoseHead',
        deconv_setting=[16, 24, 24],
        num_deconv_layers=3,
        num_deconv_kernels=[4, 4, 4],
        num_joints=channel_cfg['dataset_joints'],
        tag_per_joint=True,
        with_heatmaps_loss=[True, True],
        with_ae_loss=[True, False],
        channels=(16, 16, 32, 48, 80),
        loss_keypoint=dict(
            type='MultiLossFactory',
            num_joints=channel_cfg['dataset_joints'],
            num_stages=2,
            ae_loss_type='exp',
            with_ae_loss=[True, False],
            push_loss_factor=[0.001, 0.001],
            pull_loss_factor=[0.001, 0.001],
            with_heatmaps_loss=[True, True],
            heatmaps_loss_factor=[1.0, 1.0])),
    train_cfg=dict(),
    test_cfg=dict(
        num_joints=channel_cfg['dataset_joints'],
        max_num_people=30,
        scale_factor=[1],
        with_heatmaps=[True, True],
        with_ae=[True, False],
        project2image=True,
        align_corners=False,
        nms_kernel=5,
        nms_padding=2,
        tag_per_joint=True,
        detection_threshold=0.1,
        tag_threshold=1,
        use_detection_val=True,
        ignore_too_much=False,
        adjust=True,
        refine=True,
        flip_test=True))

train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='BottomUpRandomAffine',
        rot_factor=30,
        scale_factor=[0.75, 1.5],
        scale_type='short',
        trans_factor=40),
    dict(type='BottomUpRandomFlip', flip_prob=0.5),
    dict(type='ToTensor'),
    dict(
        type='NormalizeTensor',
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]),
    dict(
        type='BottomUpGenerateTarget',
        sigma=2,
        max_num_people=30,
    ),
    dict(
        type='Collect',
        keys=['img', 'joints', 'targets', 'masks'],
        meta_keys=[]),
]

val_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='BottomUpGetImgSize', test_scale_factor=[1]),
    dict(
        type='BottomUpResizeAlign',
        transforms=[
            dict(type='ToTensor'),
            dict(
                type='NormalizeTensor',
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]),
        ]),
    dict(
        type='Collect',
        keys=['img'],
        meta_keys=[
            'image_file', 'aug_data', 'test_scale_factor', 'base_size',
            'center', 'scale', 'flip_index'
        ]),
]

test_pipeline = val_pipeline

data_root = 'data/crowdpose'
data = dict(
    workers_per_gpu=4,
    train_dataloader=dict(samples_per_gpu=32),
    val_dataloader=dict(samples_per_gpu=1),
    test_dataloader=dict(samples_per_gpu=1),
    train=dict(
        type='BottomUpCrowdPoseDataset',
        ann_file=f'{data_root}/annotations/mmpose_crowdpose_trainval.json',
        img_prefix=f'{data_root}/images/',
        data_cfg=data_cfg,
        pipeline=train_pipeline,
        dataset_info={{_base_.dataset_info}}),
    val=dict(
        type='BottomUpCrowdPoseDataset',
        ann_file=f'{data_root}/annotations/mmpose_crowdpose_test.json',
        img_prefix=f'{data_root}/images/',
        data_cfg=data_cfg,
        pipeline=val_pipeline,
        dataset_info={{_base_.dataset_info}}),
    test=dict(
        type='BottomUpCrowdPoseDataset',
        ann_file=f'{data_root}/annotations/mmpose_crowdpose_test.json',
        img_prefix=f'{data_root}/images/',
        data_cfg=data_cfg,
        pipeline=test_pipeline,
        dataset_info={{_base_.dataset_info}}),
)