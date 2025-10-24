import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo
    import matplotlib.pyplot as plt

    # 示例数据
    categories = ['A', 'B', 'C', 'D']
    values = [25, 40, 30, 35]

    # 创建条形图
    plt.figure(figsize=(8, 5)) # 设置图表大小
    plt.bar(categories, values, color=['#ff6b6b', '#51cf66', '#fcc419', '#339af0']) # 绘制条形图并设置颜色

    # 装饰图表
    plt.title('Sample Bar Chart', fontsize=14) # 添加标题
    plt.xlabel('Categories', fontsize=12) # 添加X轴标签
    plt.ylabel('Values', fontsize=12) # 添加Y轴标签

    # 显示图表
    plt.show()
    return


if __name__ == "__main__":
    app.run()
