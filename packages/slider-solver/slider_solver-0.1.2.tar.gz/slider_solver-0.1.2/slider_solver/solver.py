def solve_slider(bg, cut, bg_size=None, cut_size=None):
    from PIL import Image
    import cv2
    import numpy as np

    # 如果是路径，打开图片
    if isinstance(bg, str):
        bg_img = Image.open(bg)
    else:
        bg_img = bg

    if isinstance(cut, str):
        cut_img = Image.open(cut)
    else:
        cut_img = cut

    # 转 OpenCV
    bg_cv = cv2.cvtColor(np.array(bg_img), cv2.COLOR_RGB2BGR)

    if cut_img.mode == "RGBA":
        cut_arr = np.array(cut_img)
        alpha = cut_arr[:, :, 3]
        mask = alpha > 128
        new_cut = np.zeros_like(cut_arr[:, :, :3], dtype=np.uint8)
        new_cut[mask] = cut_arr[:, :, :3][mask]
        cut_cv = cv2.cvtColor(new_cut, cv2.COLOR_RGB2BGR)
    else:
        cut_cv = cv2.cvtColor(np.array(cut_img), cv2.COLOR_RGB2BGR)

    # 缩放
    if bg_size:
        bg_cv = cv2.resize(bg_cv, bg_size, interpolation=cv2.INTER_AREA)
    if cut_size:
        cut_cv = cv2.resize(cut_cv, cut_size, interpolation=cv2.INTER_AREA)

    # 灰度 & 边缘
    bg_edge = cv2.Canny(cv2.cvtColor(bg_cv, cv2.COLOR_BGR2GRAY), 100, 200)
    cut_edge = cv2.Canny(cv2.cvtColor(cut_cv, cv2.COLOR_BGR2GRAY), 100, 200)

    # 模板匹配
    _, _, _, max_loc = cv2.minMaxLoc(cv2.matchTemplate(bg_edge, cut_edge, cv2.TM_CCOEFF_NORMED))
    x_found, _ = max_loc
    move_x = int(round(x_found * (bg_img.width / bg_cv.shape[1])))
    return move_x
