import type { ChartTable } from './theme'

/** Accessible data view rendered under each data-driven figure. */
export default function ChartDataTable({ table }: { table: ChartTable }) {
  return (
    <details className="mt-3 text-sm text-neutral-600">
      <summary className="cursor-pointer select-none font-medium text-neutral-700 hover:text-[#080c04]">
        Show data
      </summary>
      <div className="mt-2 max-h-64 overflow-auto rounded-lg border border-neutral-200">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-neutral-50">
            <tr>
              {table.header.map((h) => (
                <th key={h} className="px-3 py-2 font-semibold text-neutral-700">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, i) => (
              <tr key={i} className="border-t border-neutral-100">
                {row.map((cell, j) => (
                  <td key={j} className="px-3 py-1.5 tabular-nums">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}
