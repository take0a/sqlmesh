import { window } from 'vscode'
import { AuthenticationProviderTobikoCloud } from '../auth/auth'
import { signIn } from '../commands/signin'
import { traceInfo } from './common/log'

/**
 * Represents different types of errors that can occur in the application.
 * アプリケーションで発生する可能性のあるさまざまな種類のエラーを表します。
 */
export type ErrorType =
  | ErrorTypeGeneric
  | { type: 'not_signed_in' }
  | { type: 'sqlmesh_not_found' }
  | { type: 'sqlmesh_lsp_not_found' }
  // tcloud_bin_not_found is used when the tcloud executable is not found. This is likely to happen if the user
  // opens a project that has a `tcloud.yaml` file but doesn't have tcloud installed.
  // tcloud_bin_not_found は、tcloud 実行ファイルが見つからない場合に使用されます。
  // これは、ユーザーが `tcloud.yaml` ファイルがあるプロジェクトを開いたものの、
  // tcloud がインストールされていない場合に発生する可能性があります。
  | { type: 'tcloud_bin_not_found' }
  | SqlmeshLspDependenciesMissingError
  | ErrorTypeInvalidState
  | ErrorTypeSQLMeshOutdated

/**
 * ErrorTypeSQLMeshOutdated is used when the SQLMesh version is outdated. The
 * message should explain the problem, but the suggestion to update SQLMesh is
 * handled at the place where the error is shown.
 * ErrorTypeSQLMeshOutdated は、SQLMesh のバージョンが古い場合に使用されます。
 * メッセージには問題の説明が表示されますが、SQLMesh の更新の提案は
 * エラーが表示された場所で処理されます。
 */
export interface ErrorTypeSQLMeshOutdated {
  type: 'sqlmesh_outdated'
  /**
   * A message that describes the outdated SQLMesh version, it should not talk about
   * updating SQLMesh. This is done at the place where the error is handled.
   * SQLMeshのバージョンが古いことを示すメッセージです。
   * SQLMeshのアップデートについては言及すべきではありません。これはエラー処理時に行われます。
   */
  message: string
}

/**
 * ErrorTypeInvalidState is used when the state of the application is invalid state.
 * They should never be thrown by the application unless there is a bug in the code.
 * The shown message should be generic and not contain any sensitive information but
 * asks the user to report the issue to the developers.
 * ErrorTypeInvalidState は、アプリケーションの状態が無効な場合に使用されます。
 * コードにバグがない限り、アプリケーションによってこれらのエラーがスローされることはありません。
 * 表示されるメッセージは一般的な内容で、機密情報は含まず、ユーザーに開発者に問題を報告するよう
 * 求める内容である必要があります。
 */
export interface ErrorTypeInvalidState {
  type: 'invalid_state'
  /**
   * A message that describes the invalid state, it should not talk about reporting
   * the issue to the developers. This is done at the place where the error is
   * handled.
   * 無効な状態を説明するメッセージであり、開発者に問題を報告することについては言及すべきではありません。
   * これはエラーが処理される場所で行われます。
   */
  message: string
}

/**
 * ErrorTypeGeneric is a generic error type that can be used to represent any error with a message.
 * ErrorTypeGeneric は、メッセージを使用してあらゆるエラーを表すために使用できる汎用エラー タイプです。
 */
export interface ErrorTypeGeneric {
  type: 'generic'
  message: string
}

/**
 * SqlmeshLspDependenciesMissingError is used when the sqlmesh_lsp is found but
 * the lsp extras are missing.
 * SqlmeshLspDependenciesMissingError は、sqlmesh_lsp が見つかったが、
 * lsp 追加情報が見つからない場合に使用されます。
 */
interface SqlmeshLspDependenciesMissingError {
  type: 'sqlmesh_lsp_dependencies_missing'
  is_missing_pygls: boolean
  is_missing_lsprotocol: boolean
  is_tobiko_cloud: boolean
}

export async function handleError(
  authProvider: AuthenticationProviderTobikoCloud,
  restartLsp: () => Promise<void>,
  error: ErrorType,
  genericErrorPrefix?: string,
): Promise<void> {
  traceInfo('handleError', error)
  switch (error.type) {
    case 'invalid_state':
      await window.showErrorMessage(
        `Invalid state: ${error.message}. Please report this issue to the developers.`,
      )
      return
    case 'sqlmesh_outdated':
      await window.showErrorMessage(
        `SQLMesh itself is outdated. Please update SQLMesh to the latest version to use this feature. ${error.message}`,
      )
      return
    case 'not_signed_in':
      return handleNotSignedInError(authProvider, restartLsp)
    case 'sqlmesh_not_found':
      return handleSqlmeshNotFoundError()
    case 'sqlmesh_lsp_not_found':
      return handleSqlmeshLspNotFoundError()
    case 'sqlmesh_lsp_dependencies_missing':
      return handleSqlmeshLspDependenciesMissingError(error)
    case 'tcloud_bin_not_found':
      return handleTcloudBinNotFoundError()
    case 'generic':
      if (genericErrorPrefix) {
        await window.showErrorMessage(`${genericErrorPrefix}: ${error.message}`)
      } else {
        await window.showErrorMessage(`An error occurred: ${error.message}`)
      }
      return
  }
}

/**
 * Handles the case where the user is not signed in to Tobiko Cloud.
 * ユーザーが Tobiko Cloud にサインインしていない場合を処理します。
 * @param authProvider - The authentication provider to use for signing in.
 */
const handleNotSignedInError = async (
  authProvider: AuthenticationProviderTobikoCloud,
  restartLsp: () => Promise<void>,
): Promise<void> => {
  traceInfo('handleNotSginedInError')
  const result = await window.showInformationMessage(
    'Please sign in to Tobiko Cloud to use SQLMesh',
    'Sign In',
  )
  if (result === 'Sign In') {
    await signIn(authProvider, restartLsp)()
  }
}

/**
 * Handles the case where the sqlmesh executable is not found.
 * sqlmesh 実行可能ファイルが見つからない場合を処理します。
 */
const handleSqlmeshNotFoundError = async (): Promise<void> => {
  traceInfo('handleSqlmeshNotFoundError')
  await window.showErrorMessage('SQLMesh not found, please check installation')
}

/**
 * Handles the case where the sqlmesh_lsp is not found.
 * sqlmesh_lsp が見つからないケースを処理します。
 */
const handleSqlmeshLspNotFoundError = async (): Promise<void> => {
  traceInfo('handleSqlmeshLspNotFoundError')
  await window.showErrorMessage(
    'SQLMesh LSP not found, please check installation',
  )
}

/**
 * Handles the case where the sqlmesh_lsp is found but the lsp extras are missing.
 * sqlmesh_lsp は見つかったが、lsp エクストラが見つからないケースを処理します。
 */
const handleSqlmeshLspDependenciesMissingError = async (
  error: SqlmeshLspDependenciesMissingError,
): Promise<void> => {
  traceInfo('handleSqlmeshLspDependenciesMissingError')
  if (error.is_tobiko_cloud) {
    await window.showErrorMessage(
      'LSP dependencies missing, make sure to include `lsp` in the `extras` section of your `tcloud.yaml` file.',
    )
  } else {
    const install = await window.showErrorMessage(
      'LSP dependencies missing, make sure to install `sqlmesh[lsp]`.',
      'Install',
    )
    if (install === 'Install') {
      const terminal = window.createTerminal({
        name: 'SQLMesh LSP Install',
        hideFromUser: false,
      })
      terminal.show()
      terminal.sendText("pip install 'sqlmesh[lsp]'", false)
    }
  }
}

/**
 * Handles the case where the tcloud executable is not found.
 * tcloud 実行ファイルが見つからない場合を処理します。
 */
const handleTcloudBinNotFoundError = async (): Promise<void> => {
  const result = await window.showErrorMessage(
    'tcloud executable not found, please check installation',
    'Install',
  )
  if (result === 'Install') {
    const terminal = window.createTerminal({
      name: 'Tcloud Install',
      hideFromUser: false,
    })
    terminal.show()
    terminal.sendText('pip install tcloud', false)
  }
}
