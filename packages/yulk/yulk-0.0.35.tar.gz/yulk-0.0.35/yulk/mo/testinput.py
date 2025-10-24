import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk 
    return


@app.cell
def _():
    import marimo as mo

    def handle_button_click(_): return mo.md(text_input.value)

    text_input = mo.ui.text(
        placeholder="在这里输入内容...",
        label="输入框"
    )

    button = mo.ui.button(
        label="点击显示",
        on_click=handle_button_click  # 绑定处理函数
    )

    mo.vstack([text_input, button])
    return


if __name__ == "__main__":
    app.run()
