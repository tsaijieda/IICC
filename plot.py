import sys
import yaml
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['PingFang TC', 'Heiti TC', 'Arial Unicode MS'] 
plt.rcParams['axes.unicode_minus'] = False  # 確保坐標軸的負號正常顯示

# 1. 檢查命令列參數是否包含檔案名稱
if len(sys.argv) < 2:
    print("用法: python plot.py <你的檔案名稱.yaml>")
    sys.exit(1)

# 取得傳入的檔案名稱
filename = sys.argv[1]

# 2. 讀取 YAML 檔案
try:
    with open(filename, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
except FileNotFoundError:
    print(f"錯誤: 找不到檔案 '{filename}'")
    sys.exit(1)

# 3. 建立畫布
plt.figure(figsize=(8, 5))

# 迴圈讀取並繪製每一條軌跡
for entity in data.get('entities', []):
    times = [point[0] for point in entity['trajectory']]
    depths = [point[1] for point in entity['trajectory']]
    
    # 畫線與端點
    plt.plot(times, depths, 
             color=entity['color'], 
             linestyle=entity['linestyle'], 
             label=entity['label'],
             marker='o')

# 4. 基本圖表設定 (使用 get 避免 yaml 缺漏屬性報錯)
plt.title(data.get('title', 'Tactical Diagram'))
plt.xlabel(data.get('x_label', 'Time'))
plt.ylabel(data.get('y_label', 'Field Depth'))

if 'x_limits' in data:
    plt.xlim(data['x_limits'])
if 'y_limits' in data:
    plt.ylim(data['y_limits'])

# 開啟網格並顯示圖例
plt.grid(True)
plt.legend()

# 顯示圖片
plt.tight_layout()
plt.show()
