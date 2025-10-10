import * as vscode from 'vscode'
import { LSPClient } from '../lsp/lsp'
import { isErr } from '@bus/result'
import { RenderModelEntry } from '../lsp/custom'
import { RenderedModelProvider } from '../providers/renderedModelProvider'

export async function reRenderModelForSourceFile(
  sourceUri: string,
  lspClient: LSPClient | undefined,
  renderedModelProvider: RenderedModelProvider,
): Promise<void> {
  const renderedUri = renderedModelProvider.getRenderedUriForSource(sourceUri)
  if (!renderedUri) {
    return // No rendered model exists for this source file
           // このソースファイルにはレンダリングされたモデルが存在しません
  }
  if (!lspClient) {
    return
  }

  // Call the render model API
  // レンダリングモデルAPIを呼び出す
  const result = await lspClient.call_custom_method('sqlmesh/render_model', {
    textDocumentUri: sourceUri,
  })

  if (isErr(result)) {
    // Silently fail on auto-rerender errors to avoid spamming user
    // 自動再レンダリングエラーが発生した場合、ユーザーに迷惑をかけないように、サイレントに失敗します。
    return
  }

  // Check if we got any models
  // モデルがあるか確認する
  if (!result.value.models || result.value.models.length === 0) {
    return
  }

  // Get the originally rendered model information
  // 元々レンダリングされたモデル情報を取得する
  const originalModelInfo =
    renderedModelProvider.getModelInfoForRendered(renderedUri)

  // Find the specific model that was originally rendered, or fall back to the first model
  // 最初にレンダリングされた特定のモデルを見つけるか、最初のモデルにフォールバックします
  const selectedModel = originalModelInfo
    ? result.value.models.find(
        model =>
          model.name === originalModelInfo.name &&
          model.fqn === originalModelInfo.fqn,
      ) || result.value.models[0]
    : result.value.models[0]

  // Update the existing rendered model content
  // 既存のレンダリングされたモデルコンテンツを更新する
  renderedModelProvider.updateRenderedModel(
    renderedUri,
    selectedModel.rendered_query,
  )
}

export function renderModel(
  lspClient?: LSPClient,
  renderedModelProvider?: RenderedModelProvider,
) {
  return async () => {
    if (!lspClient) {
      vscode.window.showErrorMessage('LSP client not available')
      return
    }

    // Get the current active editor
    // 現在アクティブなエディターを取得する
    const activeEditor = vscode.window.activeTextEditor

    let documentUri: string

    if (!activeEditor) {
      // No active editor, show a list of all models
      // アクティブなエディタがありません。すべてのモデルのリストを表示します。
      const allModelsResult = await lspClient.call_custom_method(
        'sqlmesh/all_models_for_render',
        {},
      )

      if (isErr(allModelsResult)) {
        vscode.window.showErrorMessage(
          `Failed to get models: ${allModelsResult.error.message}`,
        )
        return
      }

      if (
        !allModelsResult.value.models ||
        allModelsResult.value.models.length === 0
      ) {
        vscode.window.showInformationMessage('No models found in the project')
        return
      }

      // Let user choose from all models
      // ユーザーがすべてのモデルから選択できるようにする
      const items = allModelsResult.value.models.map(model => ({
        label: model.name,
        description: model.fqn,
        detail: model.description ? model.description : undefined,
        model: model,
      }))

      const selected = await vscode.window.showQuickPick(items, {
        placeHolder: 'Select a model to render',
      })

      if (!selected) {
        return
      }

      // Use the selected model's URI
      // 選択したモデルのURIを使用する
      documentUri = selected.model.uri
    } else {
      // Get the current document URI
      // 現在のドキュメントURIを取得する
      documentUri = activeEditor.document.uri.toString(true)
    }

    // Call the render model API
    // レンダリングモデルAPIを呼び出す
    const result = await lspClient.call_custom_method('sqlmesh/render_model', {
      textDocumentUri: documentUri,
    })

    if (isErr(result)) {
      vscode.window.showErrorMessage(
        `Failed to render model: ${result.error.message}`,
      )
      return
    }

    // Check if we got any models
    // モデルがあるか確認する
    if (!result.value.models || result.value.models.length === 0) {
      vscode.window.showInformationMessage(
        'No models found in the current file',
      )
      return
    }

    // If multiple models, let user choose
    // 複数のモデルがある場合は、ユーザーに選択させる
    let selectedModel: RenderModelEntry
    if (result.value.models.length > 1) {
      const items = result.value.models.map(model => ({
        label: model.name,
        description: model.fqn,
        detail: model.description ? model.description : undefined,
        model: model,
      }))

      const selected = await vscode.window.showQuickPick(items, {
        placeHolder: 'Select a model to render',
      })

      if (!selected) {
        return
      }

      selectedModel = selected.model
    } else {
      selectedModel = result.value.models[0]
    }

    if (!renderedModelProvider) {
      vscode.window.showErrorMessage('Rendered model provider not available')
      return
    }

    // Store the rendered content and get a virtual URI
    // レンダリングされたコンテンツを保存し、仮想URIを取得する
    const uri = renderedModelProvider.storeRenderedModel(
      selectedModel.name,
      selectedModel.rendered_query,
      documentUri,
      selectedModel,
    )

    // Open the virtual document
    // 仮想ドキュメントを開く
    const document = await vscode.workspace.openTextDocument(uri)

    // Determine the view column for side-by-side display
    // Find the rightmost column with an editor
    // 並べて表示するためのビュー列を決定します
    // エディターで右端の列を見つけます
    let maxColumn = vscode.ViewColumn.One
    for (const editor of vscode.window.visibleTextEditors) {
      if (editor.viewColumn && editor.viewColumn > maxColumn) {
        maxColumn = editor.viewColumn
      }
    }

    // Open in the next column after the rightmost editor
    // 右端のエディタの次の列で開く
    const viewColumn = maxColumn + 1

    // Open the document in the editor as a preview (preview: true is default)
    // ドキュメントをエディターでプレビューとして開きます（preview: true がデフォルト）
    await vscode.window.showTextDocument(document, {
      viewColumn: viewColumn,
      preview: true,
      preserveFocus: false,
    })

    // Execute "Keep Open" command to convert preview tab to permanent tab
    // 「開いたままにする」コマンドを実行して、プレビュータブを永続的なタブに変換します。
    await vscode.commands.executeCommand('workbench.action.keepEditor')

    // Explicitly set the language mode to SQL for syntax highlighting
    // 構文の強調表示のために言語モードを明示的にSQLに設定する
    await vscode.languages.setTextDocumentLanguage(document, 'sql')
  }
}
