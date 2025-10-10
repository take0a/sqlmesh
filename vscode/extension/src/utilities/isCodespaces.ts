/**
 * isCodespaces checks if the current environment is a Codespaces
 * isCodespacesは現在の環境がCodespacesであるかどうかを確認します
 *
 * @returns true if the current environment is a Codespaces, false otherwise
 */
export const isCodespaces = () => {
  return (
    process.env.CODESPACES === 'true' || !!process.env.GITHUB_CODESPACE_TOKEN
  )
}
