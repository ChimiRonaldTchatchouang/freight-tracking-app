interface AlertProps {
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
}

export function Alert({ type, title, message }: AlertProps) {
  const colors = {
    success: 'bg-green-50 text-green-800 border-green-200',
    error: 'bg-red-50 text-red-800 border-red-200',
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    info: 'bg-blue-50 text-blue-800 border-blue-200'
  }
  
  return (
    <div className={`p-4 rounded-lg border ${colors[type]}`}>
      <h3 className="font-semibold">{title}</h3>
      <p className="text-sm">{message}</p>
    </div>
  )
}
