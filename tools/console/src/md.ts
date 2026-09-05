import { Marked } from 'marked'
import type { Tokens } from 'marked'

/** 渲染 SKILL.md：去 frontmatter；给二级标题编号 id（h-0, h-1 …）供页内目录跳转。 */
export async function renderSkill(markdown: string): Promise<{ html: string; headings: string[] }> {
  const md = markdown.replace(/^---\n[\s\S]*?\n---\n/, '')
  const headings: string[] = []
  const marked = new Marked({
    renderer: {
      heading(this: { parser: { parseInline: (t: Tokens.Generic[]) => string } }, token: Tokens.Heading) {
        const text = this.parser.parseInline(token.tokens)
        if (token.depth === 2) {
          const id = `h-${headings.length}`
          headings.push(token.text)
          return `<h2 id="${id}">${text}</h2>\n`
        }
        return `<h${token.depth}>${text}</h${token.depth}>\n`
      },
    },
  })
  const html = await marked.parse(md)
  return { html, headings }
}
