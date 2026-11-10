import React from 'react'

import type { ResearchTable } from '@/types/research'

export default function ResearchTableView({ table }: { table: ResearchTable }) {
  return (
    <figure id={table.id} className="my-10 scroll-mt-24">
      <figcaption className="mb-3 text-sm leading-relaxed text-ink-soft">
        <span className="font-semibold text-ink">Table {table.number}.</span> {table.caption}
      </figcaption>
      <div className="overflow-x-auto rounded-xl border border-rule bg-white">
        <table className="w-full min-w-[640px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-ink/20 bg-panel text-ink">
              {table.header.map((h, i) => (
                <th
                  key={h}
                  scope="col"
                  className={
                    i === 0 ? 'px-4 py-3 font-semibold' : 'px-4 py-3 text-right font-semibold'
                  }
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row) => (
              <tr key={row[0]} className="border-t border-neutral-100 even:bg-panel/50">
                {row.map((cell, i) =>
                  i === 0 ? (
                    <th key={i} scope="row" className="px-4 py-2.5 font-medium text-ink">
                      {cell}
                    </th>
                  ) : (
                    <td
                      key={i}
                      className="whitespace-nowrap px-4 py-2.5 text-right tabular-nums text-ink-soft"
                    >
                      {cell}
                    </td>
                  )
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  )
}
