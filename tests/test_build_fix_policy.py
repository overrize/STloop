from stloop.build_fix_policy import should_attempt_main_c_fix


def test_skip_fix_for_linker_or_cmake_infra_errors():
    ok, reason = should_attempt_main_c_fix("CMake Error: No linker script .ld found")
    assert ok is False
    assert "基础设施问题" in reason


def test_allow_fix_for_c_compile_errors():
    ok, reason = should_attempt_main_c_fix("main.c:32:5: error: 'LL_RCC_HSE_Enable' undeclared")
    assert ok is True
    assert "代码错误" in reason

