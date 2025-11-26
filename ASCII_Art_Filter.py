import cv2
import numpy as np
import pyautogui
import time
import tkinter as tk

# ASCII 문자 집합 (어두움 → 밝음)
ASCII_CHARS = "@$#!~+- "

# Tkinter 캡처 영역 선택
root = tk.Tk()
root.attributes("-fullscreen", True)   # 전체화면
root.attributes("-alpha", 0.3)   # 반투명
root.configure(bg='black')

ref_point = []
rect_id = None

def on_button_press(event):
    # 드래그 시작 좌표
    global ref_point, rect_id
    ref_point = [(event.x, event.y)]
    rect_id = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=2)

def on_mouse_move(event):
    # 드래그 중 사각형 크기 업데이트
    global rect_id
    if rect_id:
        x0, y0 = ref_point[0]
        canvas.coords(rect_id, x0, y0, event.x, event.y)

def on_button_release(event):
    # 드래그 종료 → 좌표 저장 후 종료
    global ref_point
    ref_point.append((event.x, event.y))
    root.quit()

canvas = tk.Canvas(root, bg='black')
canvas.pack(fill=tk.BOTH, expand=True)
canvas.bind("<ButtonPress-1>", on_button_press)
canvas.bind("<B1-Motion>", on_mouse_move)
canvas.bind("<ButtonRelease-1>", on_button_release)

root.mainloop()
root.destroy()

# 선택된 영역 좌표 계산
x1, y1 = ref_point[0]
x2, y2 = ref_point[1]
x, y = min(x1, x2), min(y1, y2)
w, h = abs(x2 - x1), abs(y2 - y1)
print(f"선택 영역: x={x}, y={y}, w={w}, h={h}")

# ASCII 변환
def frame_to_ascii_fixed_char(frame, char_width=10, font_ratio=0.6, target_cols=None, resize_ratio=0.5):

    # 프레임 축소 (메모리 최적화)
    frame_small = cv2.resize(frame, (0, 0), fx=resize_ratio, fy=resize_ratio, interpolation=cv2.INTER_AREA)

    # 그레이스케일 변환
    gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape

    # 글자 픽셀 크기
    cell_width = max(char_width, 1)
    cell_height = max(int(cell_width * font_ratio), 1)

    # 목표 글자 수가 있을 경우 우선 적용
    if target_cols:
        max_cols = width // 2
        cols = min(max(target_cols, 10), max_cols)
        cell_width = max(width // cols, 1)
        cell_height = max(int(cell_width * font_ratio), 1)
    else:
        cols = max(width // cell_width, 1)

    rows = max(height // cell_height, 1)

    # 셀 크기 맞춰 이미지 자르기
    usable_width = cols * cell_width
    usable_height = rows * cell_height
    gray = gray[:usable_height, :usable_width]

    # 셀 단위 평균 밝기 계산
    gray_cells = gray.reshape(rows, cell_height, cols, cell_width)
    avg_vals = gray_cells.mean(axis=(1, 3))

    # 밝기 → ASCII 문자 인덱스 매핑
    indices = (avg_vals / 255 * (len(ASCII_CHARS) - 1)).astype(int)
    ascii_image = "\n".join("".join(ASCII_CHARS[idx] for idx in row) for row in indices)

    return ascii_image, cols, rows, cell_width, cell_height

# ASCII → 이미지 렌더링
def ascii_to_image(ascii_str, cols, rows, cell_width, cell_height):
    lines = ascii_str.splitlines()

    img_width = cols * cell_width
    img_height = rows * cell_height

    # 배경 흰색
    img = np.ones((img_height, img_width, 3), dtype=np.uint8) * 255

    color = (0, 0, 0)   # 글자 색상
    thickness = 1
    font_scale = cell_width / 10

    # 문자 하나씩 그리기
    for i, line in enumerate(lines):
        y = int((i + 1) * cell_height)
        for j, c in enumerate(line):
            x = int(j * cell_width)
            cv2.putText(img, c, (x, y), cv2.FONT_HERSHEY_PLAIN, font_scale, color, thickness, lineType=cv2.LINE_AA)
    return img

# 메인 루프
fps_limit = 60
prev_time = 0

char_width = 10
font_ratio = 0.6
target_cols = None

resize_ratio = 0.5
window_scale = 1.0
scale_step = 0.1

while True:
    # FPS 제한
    current_time = time.time()
    if current_time - prev_time < 1 / fps_limit:
        continue
    prev_time = current_time

    # 화면 캡처
    screenshot = pyautogui.screenshot(region=(x, y, w, h))
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # ASCII 변환
    ascii_frame, cols, rows, cell_width, cell_height = frame_to_ascii_fixed_char(frame, char_width, font_ratio, target_cols, resize_ratio)

    # ASCII → 이미지 변환
    img_ascii = ascii_to_image(ascii_frame, cols, rows, cell_width, cell_height)

    # 원본 해상도 비율로 복원
    img_ascii = cv2.resize(
        img_ascii,
        (int(img_ascii.shape[1] / resize_ratio),
         int(img_ascii.shape[0] / resize_ratio)),
        interpolation=cv2.INTER_LINEAR
    )

    # 출력 창 스케일 조절
    if window_scale != 1.0:
        img_ascii = cv2.resize(
            img_ascii,
            (int(img_ascii.shape[1] * window_scale),
             int(img_ascii.shape[0] * window_scale)),
            interpolation=cv2.INTER_LINEAR
        )

    # 출력
    cv2.imshow("ASCII ART Filter", img_ascii)

    # 키 입력 처리
    key = cv2.waitKey(1)

    if key == 27 or cv2.getWindowProperty("ASCII ART Filter", cv2.WND_PROP_VISIBLE) < 1:  # 종료
        break
    elif key == ord(','):   # 글자 수 증가
        target_cols = cols + 10
    elif key == ord('.'):   # 글자 수 감소
        target_cols = max(cols - 10, 10)
    elif key == ord(']'):   # 창 확대
        window_scale += scale_step
    elif key == ord('['):   # 창 축소
        window_scale = max(window_scale - scale_step, 0.1)

cv2.destroyAllWindows()
