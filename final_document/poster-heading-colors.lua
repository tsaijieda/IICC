-- Color poster headings for PDF (used by pandoc, not edited in poster.md).

local colors = {
  [1] = "2E7D32",
  [2] = "1565C0",
  [3] = "E65100",
}

local commands = {
  [1] = "\\section",
  [2] = "\\subsection",
  [3] = "\\subsubsection",
}

function Header(el)
  local hex = colors[el.level]
  local cmd = commands[el.level]
  if not hex or not cmd then
    return el
  end

  local text = pandoc.utils.stringify(el)
  return pandoc.RawBlock(
    "latex",
    cmd .. "{\\textcolor[HTML]{" .. hex .. "}{" .. text .. "}}"
  )
end
