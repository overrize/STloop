export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  isLoading?: boolean;
}

export interface ProjectFile {
  path: string;
  content: string;
}

export interface Project {
  id: string;
  name: string;
  board: string;
  description: string;
  files: ProjectFile[];
  createdAt: number;
}

export type Board = 
  | 'nucleo_f411re'
  | 'nucleo_f401re'
  | 'nucleo_f446re'
  | 'stm32f4_disco';

export const BOARDS: { value: Board; label: string }[] = [
  { value: 'nucleo_f411re', label: 'Nucleo F411RE' },
  { value: 'nucleo_f401re', label: 'Nucleo F401RE' },
  { value: 'nucleo_f446re', label: 'Nucleo F446RE' },
  { value: 'stm32f4_disco', label: 'STM32F4 Discovery' },
];
