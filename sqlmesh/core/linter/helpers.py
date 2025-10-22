from pathlib import Path

from sqlmesh.core.linter.rule import Range, Position
from sqlmesh.utils.pydantic import PydanticModel
from sqlglot import tokenize, TokenType, Token
import typing as t


class TokenPositionDetails(PydanticModel):
    """
    Details about a token's position in the source code in the structure provided by SQLGlot.
    SQLGlot によって提供される構造体内のソース コード内のトークンの位置に関する詳細。

    Attributes:
        line (int): The line that the token ends on.
            トークンが終了する行。
        col (int): The column that the token ends on.
            トークンが終了する列。
        start (int): The start index of the token.
            トークンの開始インデックス。
        end (int): The ending index of the token.
            トークンの終了インデックス。
    """

    line: int
    col: int
    start: int
    end: int

    @staticmethod
    def from_meta(meta: t.Dict[str, int]) -> "TokenPositionDetails":
        return TokenPositionDetails(
            line=meta["line"],
            col=meta["col"],
            start=meta["start"],
            end=meta["end"],
        )

    def to_range(self, read_file: t.Optional[t.List[str]]) -> Range:
        """
        Convert a TokenPositionDetails object to a Range object.
        TokenPositionDetails オブジェクトを Range オブジェクトに変換します。

        In the circumstances where the token's start and end positions are the same,
        there is no need for a read_file parameter, as the range can be derived from the token's
        line and column. This is an optimization to avoid unnecessary file reads and should
        only be used when the token represents a single character or position in the file.
        トークンの開始位置と終了位置が同じ場合、範囲はトークンの行と列から算出できるため、
        read_file パラメータは必要ありません。これは不要なファイル読み取りを回避するための最適化であり、
        トークンがファイル内の単一の文字または位置を表す場合にのみ使用してください。

        If the token's start and end positions are different, the read_file parameter is required.
        トークンの開始位置と終了位置が異なる場合は、read_file パラメータが必要です。

        :param read_file: List of lines from the file. Optional
            ファイルからの行のリスト。オプション
        :return: A Range object representing the token's position
            トークンの位置を表すRangeオブジェクト
        """
        if self.start == self.end:
            # If the start and end positions are the same, we can create a range directly
            # 開始位置と終了位置が同じ場合は、直接範囲を作成できます。
            return Range(
                start=Position(line=self.line - 1, character=self.col - 1),
                end=Position(line=self.line - 1, character=self.col),
            )

        if read_file is None:
            raise ValueError("read_file must be provided when start and end positions differ.")

        # Convert from 1-indexed to 0-indexed for line only
        # 行のみを 1 インデックスから 0 インデックスに変換する
        end_line_0 = self.line - 1
        end_col_0 = self.col

        # Find the start line and column by counting backwards from the end position
        # 終了位置から逆算して開始行と開始列を見つけます
        start_pos = self.start
        end_pos = self.end

        # Initialize with the end position
        # 終了位置で初期化する
        start_line_0 = end_line_0
        start_col_0 = end_col_0 - (end_pos - start_pos + 1)

        # If start_col_0 is negative, we need to go back to previous lines
        # start_col_0が負の場合、前の行に戻る必要があります
        while start_col_0 < 0 and start_line_0 > 0:
            start_line_0 -= 1
            start_col_0 += len(read_file[start_line_0])
            # Account for newline character
            # 改行文字を考慮する
            if start_col_0 >= 0:
                break
            start_col_0 += 1  # For the newline character

        # Ensure we don't have negative values
        # 負の値がないことを確認する
        start_col_0 = max(0, start_col_0)
        return Range(
            start=Position(line=start_line_0, character=start_col_0),
            end=Position(line=end_line_0, character=end_col_0),
        )


def read_range_from_string(content: str, text_range: Range) -> str:
    lines = content.splitlines(keepends=False)

    # Ensure the range is within bounds
    # 範囲が範囲内であることを確認する
    start_line = max(0, text_range.start.line)
    end_line = min(len(lines), text_range.end.line + 1)

    if start_line >= end_line:
        return ""

    # Extract the relevant portions of each line
    # 各行の関連部分を抽出する
    result = []
    for i in range(start_line, end_line):
        line = lines[i]
        start_char = text_range.start.character if i == text_range.start.line else 0
        end_char = text_range.end.character if i == text_range.end.line else len(line)
        result.append(line[start_char:end_char])

    return "".join(result)


def read_range_from_file(file: Path, text_range: Range) -> str:
    """
    Read the file and return the content within the specified range.
    ファイルを読み取り、指定された範囲内の内容を返します。

    Args:
        file: Path to the file to read
            読み取るファイルへのパス
        text_range: The range of text to extract
            抽出するテキストの範囲

    Returns:
        The content within the specified range
        指定された範囲内のコンテンツ
    """
    with file.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    return read_range_from_string("".join(lines), text_range)


def get_start_and_end_of_model_block(
    tokens: t.List[Token],
) -> t.Optional[t.Tuple[int, int]]:
    """
    Returns the start and end tokens of the MODEL block in an SQL file.
    The MODEL block is defined as the first occurrence of the keyword "MODEL" followed by
    an opening parenthesis and a closing parenthesis that matches the opening one.
    SQL ファイル内の MODEL ブロックの開始トークンと終了トークンを返します。
    MODEL ブロックは、キーワード「MODEL」の最初の出現と、それに続く開き括弧、
    および開き括弧に一致する閉じ括弧として定義されます。
    """
    # 1) Find the MODEL token
    #    MODELトークンを見つける
    try:
        model_idx = next(
            i
            for i, tok in enumerate(tokens)
            if tok.token_type is TokenType.VAR and tok.text.upper() == "MODEL"
        )
    except StopIteration:
        return None

    # 2) Find the opening parenthesis for the MODEL properties list
    #    MODELプロパティリストの開始括弧を見つけます
    try:
        lparen_idx = next(
            i
            for i in range(model_idx + 1, len(tokens))
            if tokens[i].token_type is TokenType.L_PAREN
        )
    except StopIteration:
        return None

    # 3) Find the matching closing parenthesis by looking for the first semicolon after
    # the opening parenthesis and assuming the MODEL block ends there.
    #    開き括弧の後の最初のセミコロンを探し、そこで MODEL ブロックが終了すると仮定して、
    #    対応する閉じ括弧を見つけます。
    try:
        closing_semicolon = next(
            i
            for i in range(lparen_idx + 1, len(tokens))
            if tokens[i].token_type is TokenType.SEMICOLON
        )
        # If we find a semicolon, we can assume the MODEL block ends there
        # セミコロンが見つかった場合、MODELブロックはそこで終了すると想定できます。
        rparen_idx = closing_semicolon - 1
        if tokens[rparen_idx].token_type is TokenType.R_PAREN:
            return (lparen_idx, rparen_idx)
        return None
    except StopIteration:
        return None


def get_range_of_model_block(
    sql: str,
    dialect: str,
) -> t.Optional[Range]:
    """
    Get the range of the model block in an SQL file,
    SQLファイル内のモデルブロックの範囲を取得します。
    """
    tokens = tokenize(sql, dialect=dialect)
    block = get_start_and_end_of_model_block(tokens)
    if not block:
        return None
    (start_idx, end_idx) = block
    start = tokens[start_idx - 1]
    end = tokens[end_idx + 1]
    start_position = TokenPositionDetails(
        line=start.line,
        col=start.col,
        start=start.start,
        end=start.end,
    )
    end_position = TokenPositionDetails(
        line=end.line,
        col=end.col,
        start=end.start,
        end=end.end,
    )
    splitlines = sql.splitlines()
    return Range(
        start=start_position.to_range(splitlines).start,
        end=end_position.to_range(splitlines).end,
    )


def get_range_of_a_key_in_model_block(
    sql: str,
    dialect: str,
    key: str,
) -> t.Optional[t.Tuple[Range, Range]]:
    """
    Get the ranges of a specific key and its value in the MODEL block of an SQL file.
    SQL ファイルの MODEL ブロック内の特定のキーとその値の範囲を取得します。

    Returns a tuple of (key_range, value_range) if found, otherwise None.
    見つかった場合は (key_range, value_range) のタプルを返し、見つからない場合は None を返します。
    """
    tokens = tokenize(sql, dialect=dialect)
    if not tokens:
        return None

    block = get_start_and_end_of_model_block(tokens)
    if not block:
        return None
    (lparen_idx, rparen_idx) = block

    # 4) Scan within the MODEL property list for the key at top-level (depth == 1)
    # Initialize depth to 1 since we're inside the first parentheses
    #    MODELプロパティリスト内で最上位レベルのキー（depth == 1）をスキャンします。
    #    最初の括弧内にいるので、depthを1に初期化します。
    depth = 1
    for i in range(lparen_idx + 1, rparen_idx):
        tok = tokens[i]
        tt = tok.token_type

        if tt is TokenType.L_PAREN:
            depth += 1
            continue
        if tt is TokenType.R_PAREN:
            depth -= 1
            # If we somehow exit before rparen_idx, stop early
            # rparen_idxの前に何らかの理由で終了した場合は、早めに停止する
            if depth <= 0:
                break
            continue

        if depth == 1 and tt is TokenType.VAR and tok.text.upper() == key.upper():
            # Validate key position: it should immediately follow '(' or ',' at top level
            # キーの位置を検証します。最上位レベルでは「(」または「,」の直後である必要があります。
            prev_idx = i - 1
            prev_tt = tokens[prev_idx].token_type if prev_idx >= 0 else None
            if prev_tt not in (TokenType.L_PAREN, TokenType.COMMA):
                continue

            # Key range
            lines = sql.splitlines()
            key_start = TokenPositionDetails(
                line=tok.line, col=tok.col, start=tok.start, end=tok.end
            )
            key_range = key_start.to_range(lines)

            value_start_idx = i + 1
            if value_start_idx >= rparen_idx:
                return None

            # Walk to the end of the value expression: until top-level comma or closing paren
            # Track internal nesting for (), [], {}
            # 値式の末尾まで移動します（最上位のカンマまたは閉じ括弧まで）。
            # ()、[]、{}の内部ネストを追跡します。
            nested = 0
            j = value_start_idx
            value_end_idx = value_start_idx

            def is_open(t: TokenType) -> bool:
                return t in (TokenType.L_PAREN, TokenType.L_BRACE, TokenType.L_BRACKET)

            def is_close(t: TokenType) -> bool:
                return t in (TokenType.R_PAREN, TokenType.R_BRACE, TokenType.R_BRACKET)

            while j < rparen_idx:
                ttype = tokens[j].token_type
                if is_open(ttype):
                    nested += 1
                elif is_close(ttype):
                    nested -= 1

                # End of value: at top-level (nested == 0) encountering a comma or the end paren
                # 値の終了: 最上位レベル (ネスト == 0) でコンマまたは終了括弧に遭遇
                if nested == 0 and (
                    ttype is TokenType.COMMA or (ttype is TokenType.R_PAREN and depth == 1)
                ):
                    # For comma, don't include it in the value range
                    # For closing paren, include it only if it's part of the value structure
                    # カンマは値の範囲に含めないでください
                    # 閉じ括弧は、値の構造の一部である場合にのみ含めてください
                    if ttype is TokenType.COMMA:
                        # Don't include the comma in the value range
                        # 値の範囲にカンマを含めないでください
                        break
                    else:
                        # Include the closing parenthesis in the value range
                        # 値の範囲に閉じ括弧を含める
                        value_end_idx = j
                        break

                value_end_idx = j
                j += 1

            value_start_tok = tokens[value_start_idx]
            value_end_tok = tokens[value_end_idx]

            value_start_pos = TokenPositionDetails(
                line=value_start_tok.line,
                col=value_start_tok.col,
                start=value_start_tok.start,
                end=value_start_tok.end,
            )
            value_end_pos = TokenPositionDetails(
                line=value_end_tok.line,
                col=value_end_tok.col,
                start=value_end_tok.start,
                end=value_end_tok.end,
            )
            value_range = Range(
                start=value_start_pos.to_range(lines).start,
                end=value_end_pos.to_range(lines).end,
            )

            return (key_range, value_range)

    return None
