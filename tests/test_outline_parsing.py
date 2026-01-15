import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'novel_creation_tool/ui'))

from chapter_generation_window import ChapterGenerationWindow
import tkinter as tk

root = tk.Tk()
root.withdraw()

# 测试大纲解析功能
test_outline = '''# 小说大纲：《尘境唤醒》

## 核心设定

**背景**：近未来医疗科幻 + 都市情感。现实时间线为2035年，脑机接口技术初步应用于植物人唤醒治疗。

【第一部分：尘起之时】（第1-10章）

### 第1章 深夜甜品店
**时间**：虚幻时间线起始  
**场景**：\"时光甜语\"甜品店，深夜11点  
**事件**：
- 女孩（尚未知姓名）推门而入，店内只有一位男服务员和角落的女店员  
- 她点\"回忆套餐\"，男服务员热情介绍每款甜品的寓意：\"初吻马卡龙\"\"童年提拉米苏\"\"遗憾慕斯\"  
- 女孩沉浸故事中，转头发现男服务员消失，女店员在柜台后静止  
- 她准备享用，慕斯蛋糕表面落灰，擦拭时整盘甜品化为灰烬飘散  
- 惊恐回头，女店员也化为灰尘，店铺地动山摇，她晕厥  

### 第2章 白色房间
**场景**：烂尾楼某房间，纯白墙壁，无门窗痕迹  
**事件**：
- 女孩醒来，失忆，只记得\"甜品店\"碎片  
- 尝试离开，被无形墙弹回，多次撞击无果  
- 脑海闪现模糊装饰物：车内挂饰（水晶雪花）  
- 情绪崩溃，拍打墙壁呼喊，无回应  

【第二部分：裂变之昼】（第11-20章）

### 第11章 楼层突破
**事件**：
- 小乌龟痛苦发作加剧，持续5分钟，身体局部透明化被小章鱼发现  
- 他坦白：\"每次黑夜后都更严重，我可能…在消失。\"  
- 为尽快找到出路，两人强行突破楼梯间循环  
- 方法：小章鱼闭眼数台阶，小乌龟反向行走，利用空间悖论  
- 成功抵达15楼，发现环境更破败，墙上涂鸦：\"不要睡去\"

### 第12章 神秘男子
**场景**：15楼尽头房间，满地几何符号  
**事件**：
- 遇见神秘男：50岁左右，穿着白大褂（但沾满灰尘），气质冷静  
- 他自称\"早就在这里\"，解释空间规则：
  > \"每层楼都是独立意识碎片，黑夜是碎片融合的时刻。你们能相遇，因为你们的记忆有交集。\"
- 透露关键信息：\"出路不在楼外，在你们心里。接受失去，才能得到。\"
- 赠送道具：给小章鱼红色连衣裙（\"穿上它，你会看清真相\"），给小乌龟锦囊（\"在最绝望时打开\"）'''

app = ChapterGenerationWindow(r"C:\\test\\project")  # 测试路径
print("开始解析大纲...")
app.parse_and_build_outline_tree(test_outline)
print("解析完成。")

# 检查树中的项目
tree_items = app.outline_tree.get_children()
print(f"树中项目数量: {len(tree_items)}")

for item in tree_items:
    item_text = app.outline_tree.item(item, "text")
    print(f"项目: {item_text}")
    # 检查子项目
    children = app.outline_tree.get_children(item)
    for child in children:
        child_text = app.outline_tree.item(child, "text")
        print(f"  子项目: {child_text}")
        # 检查孙子项目
        grandchildren = app.outline_tree.get_children(child)
        for grandchild in grandchildren:
            grandchild_text = app.outline_tree.item(grandchild, "text")
            print(f"    孙项目: {grandchild_text}")

root.destroy()