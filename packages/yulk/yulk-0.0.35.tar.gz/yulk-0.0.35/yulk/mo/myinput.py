import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    text_input = mo.ui.text(
        label="高级输入框",
        #value=state(),  # 将输入框的值与状态绑定
        #on_change=set_state,  # 输入变化时更新状态
        placeholder="在这里打字...",
        full_width=True,
    )
    submit_button = mo.ui.button(
        label="提交",
        on_click=lambda _: print(_, text_input.value),  # 绑定点击事件
        kind="success",  # 按钮样式，可选 'default', 'primary', 'success', 'warning', 'danger'
    )

    mo.hstack([text_input, submit_button,], align="start")
    return


if __name__ == "__main__":
    app.run()
