/**
 * Utility function that creates a promise which resolves after the specified time.
 * 指定された時間後に解決される promise を作成するユーティリティ関数。
 * @param ms The time to sleep in milliseconds
 * @returns A promise that resolves after the specified time
 */
export async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}
