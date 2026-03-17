/*
 * Zephyr-compatible Application
 * LED Blink Example using cmsis_minimal HAL
 */

#include "stm32f4xx.h"
#include "stm32f4xx_ll_gpio.h"
#include "stm32f4xx_ll_bus.h"
#include "stm32f4xx_ll_rcc.h"
#include "stm32f4xx_ll_system.h"
#include "stm32f4xx_ll_utils.h"

/* LED on PA5 (Arduino D13 on Nucleo-F411RE) */
#define LED_PIN LL_GPIO_PIN_5
#define LED_PORT GPIOA

/* Delay in milliseconds */
#define SLEEP_TIME_MS 1000

static void SystemClock_Config(void);
static void GPIO_Init(void);

int main(void)
{
    /* Configure system clock */
    SystemClock_Config();
    
    /* Initialize GPIO */
    GPIO_Init();
    
    /* Main loop */
    while (1) {
        /* Toggle LED */
        LL_GPIO_TogglePin(LED_PORT, LED_PIN);
        
        /* Delay */
        LL_mDelay(SLEEP_TIME_MS);
    }
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
static void SystemClock_Config(void)
{
    /* Enable HSE */
    LL_RCC_HSE_Enable();
    while (!LL_RCC_HSE_IsReady());
    
    /* Configure PLL: HSE * 25 / 4 = 100MHz */
    LL_RCC_PLL_ConfigDomain_SYS(LL_RCC_PLLSOURCE_HSE, LL_RCC_PLLM_DIV_4, 100, LL_RCC_PLLP_DIV_2);
    
    /* Enable PLL */
    LL_RCC_PLL_Enable();
    while (!LL_RCC_PLL_IsReady());
    
    /* Switch to PLL */
    LL_RCC_SetSysClkSource(LL_RCC_SYS_CLKSOURCE_PLL);
    while (LL_RCC_GetSysClkSource() != LL_RCC_SYS_CLKSOURCE_STATUS_PLL);
    
    /* Configure flash latency */
    LL_FLASH_SetLatency(LL_FLASH_LATENCY_3);
    
    /* Set system clock frequency */
    LL_SetSystemCoreClock(100000000);
    
    /* Configure APB prescalers */
    LL_RCC_SetAHBPrescaler(LL_RCC_SYSCLK_DIV_1);
    LL_RCC_SetAPB1Prescaler(LL_RCC_APB1_DIV_2);
    LL_RCC_SetAPB2Prescaler(LL_RCC_APB2_DIV_1);
}

/**
  * @brief GPIO Initialization
  * @retval None
  */
static void GPIO_Init(void)
{
    /* Enable GPIOA clock */
    LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOA);
    
    /* Configure PA5 as output */
    LL_GPIO_SetPinMode(LED_PORT, LED_PIN, LL_GPIO_MODE_OUTPUT);
    LL_GPIO_SetPinSpeed(LED_PORT, LED_PIN, LL_GPIO_SPEED_FREQ_LOW);
    LL_GPIO_SetPinOutputType(LED_PORT, LED_PIN, LL_GPIO_OUTPUT_PUSHPULL);
    LL_GPIO_SetPinPull(LED_PORT, LED_PIN, LL_GPIO_PULL_NO);
}
