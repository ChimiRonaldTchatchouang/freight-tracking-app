import { Button } from './Button'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  return (
    <div className="flex gap-2 items-center justify-center mt-4">
      <Button variant="secondary" onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 1}>
        Précédent
      </Button>
      <span className="px-4">Page {currentPage} / {totalPages}</span>
      <Button variant="secondary" onClick={() => onPageChange(currentPage + 1)} disabled={currentPage === totalPages}>
        Suivant
      </Button>
    </div>
  )
}
