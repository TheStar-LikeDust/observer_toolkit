# coding: utf-8


def func(**kwargs):
    # print('kwargs', kwargs)
    image = kwargs.get('image')

    # 切图
    sub_image_1 = image[0:100, 0:100]
    sub_image_2 = image[100:200, 100:200]
    sub_image_3 = image[200:300, 200:300]
    sub_image_4 = image[300:400, 300:400]
    sub_image_5 = image[400:500, 400:500]

    return [
        sub_image_1,
        sub_image_2,
        sub_image_3,
        sub_image_4,
        sub_image_5,
    ]


action_function = func

action_name = 'performance_iter'
