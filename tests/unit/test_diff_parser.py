from pr_sentinel.diff.parser import PatchParser


def test_parse_single_hunk_patch() -> None:
    patch = """@@ -10,7 +10,8 @@ public void filter()
- if (!hasPermission(user)) {
-     throw new ForbiddenException();
- }
+ // TODO: temporarily disabled
+ return true;
  chain.doFilter(request, response);
"""

    parser = PatchParser()
    hunks = parser.parse_patch(patch)

    assert len(hunks) == 1

    hunk = hunks[0]
    assert hunk.old_start == 10
    assert hunk.old_count == 7
    assert hunk.new_start == 10
    assert hunk.new_count == 8
    assert hunk.section_header == "public void filter()"

    assert len(hunk.lines) == 6

    assert hunk.lines[0].line_type == "deleted"
    assert hunk.lines[0].old_line_no == 10
    assert hunk.lines[0].new_line_no is None
    assert hunk.lines[0].content == " if (!hasPermission(user)) {"

    assert hunk.lines[3].line_type == "added"
    assert hunk.lines[3].old_line_no is None
    assert hunk.lines[3].new_line_no == 10
    assert hunk.lines[3].content == " // TODO: temporarily disabled"

    assert hunk.lines[5].line_type == "context"
    assert hunk.lines[5].old_line_no == 13
    assert hunk.lines[5].new_line_no == 12
    assert hunk.lines[5].content == " chain.doFilter(request, response);"


def test_parse_multiple_hunks_patch() -> None:
    patch = """@@ -1,3 +1,3 @@
-old one
+new one
 context
@@ -20,2 +20,3 @@ private void save()
 save();
+audit();
"""

    parser = PatchParser()
    hunks = parser.parse_patch(patch)

    assert len(hunks) == 2

    first = hunks[0]
    assert first.old_start == 1
    assert first.new_start == 1
    assert len(first.lines) == 3

    second = hunks[1]
    assert second.old_start == 20
    assert second.new_start == 20
    assert len(second.lines) == 2
    assert second.lines[1].line_type == "added"
    assert second.lines[1].new_line_no == 21


def test_parse_empty_patch_returns_empty_list() -> None:
    parser = PatchParser()

    assert parser.parse_patch(None) == []
    assert parser.parse_patch("") == []