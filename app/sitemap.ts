import { MetadataRoute } from 'next'
import { source } from '@/lib/source'

// 静态导出会在 build 阶段生成站点地图；页面列表直接来自 Fumadocs 源，
// 避免教材章节或新增指南页以后再次从手工清单中遗漏。
export const dynamic = 'force-static'
export const revalidate = false

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://langshift.dev'
  const currentDate = new Date()

  const languagePages = source.getLanguages().flatMap(({ language, pages }) =>
    pages.map((page) => ({
      url: `${baseUrl}${page.url}`,
      lastModified: currentDate,
      changeFrequency: 'weekly' as const,
      priority: page.slugs.length === 1 ? 0.9 : 0.8,
    })),
  )

  return [
    {
      url: baseUrl,
      lastModified: currentDate,
      changeFrequency: 'daily',
      priority: 1,
    },
    ...source.getLanguages().map(({ language }) => ({
      url: `${baseUrl}/${language}`,
      lastModified: currentDate,
      changeFrequency: 'daily' as const,
      priority: 0.95,
    })),
    ...languagePages,
  ]
}
