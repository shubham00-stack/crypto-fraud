import './globals.css'
import '@xyflow/react/dist/style.css'

export const metadata = {
  title: 'Crypto Fraud Attribution MVP',
  description: 'Blockchain investigation prototype'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>
}
