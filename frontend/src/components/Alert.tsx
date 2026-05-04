interface AlertProps {
  type: 'success' | 'error'
  message: string
}

export function Alert({ type, message }: AlertProps) {
  const colors = {
    success: 'bg-green-50 text-green-800 border-green-200',
    error: 'bg-red-50 text-red-800 border-red-200'
  }
  return <div className={`p-4 rounded-lg border ${colors[type]}`}>{message}</div>
}
