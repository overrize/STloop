/**
 * STLoop Demo - LED Blink (PA5)
 * STM32F411RE, LL 库
 */
#include "main.h"
#include "stm32f4xx_ll_gpio.h"
#include "stm32f4xx_ll_bus.h"
#include "stm32f4xx_ll_utils.h"

#define LED_PORT    GPIOA
#define LED_PIN     LL_GPIO_PIN_5

static void SystemClock_Config(void);
static void LED_GPIO_Init(void);

int main(void)
{
    SystemClock_Config();
    LED_GPIO_Init();

    while (1)
    {
        LL_GPIO_TogglePin(LED_PORT, LED_PIN);
        LL_mDelay(500);
    }
}

static void SystemClock_Config(void)
{
    LL_FLASH_SetLatency(LL_FLASH_LATENCY_2);
    LL_RCC_HSE_Enable();
    while (!LL_RCC_HSE_IsReady());
    LL_RCC_PLL_ConfigDomain_SYS(LL_RCC_PLLSOURCE_HSE, LL_RCC_PLLM_DIV_4, 100, LL_RCC_PLLP_DIV_2);
    LL_RCC_PLL_Enable();
    while (!LL_RCC_PLL_IsReady());
    LL_RCC_SetSysClkSource(LL_RCC_SYS_CLKSOURCE_PLL);
    while (LL_RCC_GetSysClkSource() != LL_RCC_SYS_CLKSOURCE_STATUS_PLL);
    LL_RCC_SetAHBPrescaler(LL_RCC_SYSCLK_DIV_1);
    LL_RCC_SetAPB1Prescaler(LL_RCC_APB1_DIV_2);
    LL_RCC_SetAPB2Prescaler(LL_RCC_APB2_DIV_1);
    LL_SetSystemCoreClock(100000000);
}

static void LED_GPIO_Init(void)
{
    LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOA);
    LL_GPIO_SetPinMode(LED_PORT, LED_PIN, LL_GPIO_MODE_OUTPUT);
    LL_GPIO_SetPinOutputType(LED_PORT, LED_PIN, LL_GPIO_OUTPUT_PUSHPULL);
    LL_GPIO_SetPinSpeed(LED_PORT, LED_PIN, LL_GPIO_SPEED_FREQ_LOW);
}
