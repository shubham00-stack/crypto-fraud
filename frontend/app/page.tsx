'use client'

import { useMemo, useState } from 'react'
import { Background, Controls, MarkerType, ReactFlow } from '@xyflow/react'

const API = process.env.NEXT_PUBLIC_API_URL || ''
const DEMO_WALLET = '0x1111111111111111111111111111111111111111'
const WALLET_PATTERN = /^0x[a-fA-F0-9]{40}$/

type ProgressKey = 'address' | 'network' | 'transactions' | 'graph' | 'risk'
type ProgressStep = { key: ProgressKey; label: string }
type RiskFactor = { name: string; points: number; evidence: string }
type Transaction = { tx_hash: string; chain: string; from_address: string; to_address: string; asset: string; amount: number; timestamp: string; block_number: number }
type Entity = { address: string; entity_name: string; entity_type: string; confidence: number; source: string; confirmed: boolean }
type CaseRecord = {
  id: string
  input: { title: string; victim_reference: string; blockchain: string; wallet_address: string; token: string; reported_amount: number; max_hops: number }
  valid_wallet: boolean
  transactions: Transaction[]
  entities: Entity[]
  nodes: { id: string; label: string; node_type: string; risk: number }[]
  edges: { id: string; source: string; target: string; amount: number; asset: string; tx_hash: string; timestamp: string }[]
  risk: { score: number; level: string; factors: RiskFactor[] }
  traced_amount: number
  max_hop_depth: number
  monitoring: boolean
  alerts: { id: string; severity: string; amount: number; asset: string; reason: string }[]
}

const progressSteps: ProgressStep[] = [
  { key: 'address', label: 'Address validated' },
  { key: 'network', label: 'Blockchain identified' },
  { key: 'transactions', label: 'Fetching transactions' },
  { key: 'graph', label: 'Building transaction graph' },
  { key: 'risk', label: 'Calculating risk indicators' },
]

const networkOptions = [
  { value: 'ethereum', label: 'Ethereum', available: true },
  { value: 'sepolia', label: 'Sepolia Testnet', available: true },
  { value: 'polygon', label: 'Polygon', available: true },
  { value: 'bnb', label: 'BNB Chain', available: true },
]

export default function Home() {
  const [form, setForm] = useState({ title: 'Crypto Fraud Demo Case', victim_reference: 'Victim-001', blockchain: 'ethereum', wallet_address: DEMO_WALLET, token: 'USDT', reported_amount: 250000, max_hops: 5 })
  const [caseData, setCaseData] = useState<CaseRecord | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [walletError, setWalletError] = useState('')
  const [copyState, setCopyState] = useState('Copy')
  const [progress, setProgress] = useState<ProgressKey[]>([])

  function updateForm<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm(current => ({ ...current, [key]: value }))
    if (key === 'wallet_address') setWalletError('')
  }

  function validateForm() {
    const wallet = form.wallet_address.trim()
    if (!wallet) return 'Wallet address is required.'
    if (!WALLET_PATTERN.test(wallet)) return 'Invalid Ethereum wallet address. Enter a valid 0x-prefixed 42-character address.'
    if (!form.reported_amount || form.reported_amount <= 0) return 'Reported amount must be greater than zero.'
    if (form.max_hops < 3 || form.max_hops > 5) return 'Trace depth must be between 3 and 5 hops for this demo provider.'
    return ''
  }

  async function analyze() {
    const validationError = validateForm()
    if (validationError) {
      const isWalletError = validationError.includes('wallet') || validationError.includes('Wallet')
      setWalletError(isWalletError ? validationError : '')
      setError(isWalletError ? '' : validationError)
      return
    }
    setBusy(true)
    setError('')
    setWalletError('')
    setCaseData(null)
    setProgress(['address', 'network'])
    try {
      const res = await fetch(`${API}/api/cases`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Unable to fetch blockchain data. Please verify the network and wallet address, then try again.')
      }
      setProgress(['address', 'network', 'transactions'])
      const data = await res.json() as CaseRecord
      setProgress(['address', 'network', 'transactions', 'graph', 'risk'])
      setCaseData(data)
    } catch (e) {
      const message = e instanceof TypeError
        ? 'Unable to connect to the analysis service. Make sure the backend is running on port 8000.'
        : e instanceof Error && e.message
          ? e.message
          : 'Unable to complete analysis. Please try again.'
      setError(message)
      setProgress([])
    } finally { setBusy(false) }
  }

  async function monitor() {
    if (!caseData) return
    try {
      const res = await fetch(`${API}/api/cases/${caseData.id}/monitor/start`, { method: 'POST' })
      if (!res.ok) throw new Error('Monitoring could not be started.')
      setCaseData(await res.json() as CaseRecord)
    } catch (e) { setError(e instanceof Error ? e.message : 'Monitoring could not be started.') }
  }

  async function copyWallet() {
    try {
      await navigator.clipboard.writeText(form.wallet_address)
      setCopyState('Copied')
      window.setTimeout(() => setCopyState('Copy'), 1800)
    } catch { setCopyState('Copy failed') }
  }

  return (
    <main>
      <header className="topbar">
        <div><div className="eyebrow">INVESTIGATION PROTOTYPE</div><h1>Real-Time Crypto Fraud Attribution</h1><p className="lede">Victim report <span>→</span> wallet analysis <span>→</span> multi-hop tracing <span>→</span> exchange detection <span>→</span> risk <span>→</span> alerts <span>→</span> report</p></div>
        <div className="demoBadge"><b>DEMO MODE</b><small>Analysis uses synthetic blockchain data for demonstration.</small></div>
      </header>

      <section className="panel formPanel">
        <div className="sectionTitle"><div><div className="sectionKicker">CASE INTAKE</div><h2>1. Create Investigation Case</h2><p>Enter the reported wallet and define the scope of the trace.</p></div><span className="statusDot">● Ready</span></div>
        <div className="grid">
          <Field label="Case title"><input suppressHydrationWarning placeholder="Crypto Fraud Demo Case" value={form.title} onChange={e => updateForm('title', e.target.value)} /></Field>
          <Field label="Victim reference"><input suppressHydrationWarning placeholder="Victim-001" value={form.victim_reference} onChange={e => updateForm('victim_reference', e.target.value)} /></Field>
          <Field label="Suspect wallet address" className="wide" hint="Ethereum / EVM address"><div className={`walletInput ${walletError ? 'invalid' : WALLET_PATTERN.test(form.wallet_address) ? 'valid' : ''}`}><input suppressHydrationWarning aria-invalid={Boolean(walletError)} placeholder="0x..." value={form.wallet_address} onChange={e => updateForm('wallet_address', e.target.value)} /><button type="button" className="copyButton" onClick={copyWallet} aria-label="Copy wallet address">{copyState}</button></div>{walletError && <small className="fieldError">{walletError}</small>}</Field>
          <Field label="Blockchain network"><select suppressHydrationWarning value={form.blockchain} onChange={e => updateForm('blockchain', e.target.value)}>{networkOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select><small className="helper">All listed networks use deterministic synthetic data in demo mode.</small></Field>
          <Field label="Token"><select suppressHydrationWarning value={form.token} onChange={e => updateForm('token', e.target.value)}><option>USDT</option><option>USDC</option><option>ETH</option></select></Field>
          <Field label="Reported amount"><input suppressHydrationWarning type="number" min="1" value={form.reported_amount} onChange={e => updateForm('reported_amount', Number(e.target.value))} /></Field>
          <Field label="Trace depth"><select suppressHydrationWarning value={form.max_hops} onChange={e => updateForm('max_hops', Number(e.target.value))}>{[3, 4, 5].map(hop => <option key={hop} value={hop}>{hop} hops</option>)}</select><small className="helper">Maximum number of transaction hops to trace.</small></Field>
        </div>
        <div className="formActions"><button className="primaryButton" onClick={analyze} disabled={busy}>{busy ? 'Analyzing wallet...' : 'Analyze Wallet'} <span>→</span></button><span className="formNote">No private keys or seed phrases are required.</span></div>
        {error && <div className="error" role="alert"><b>Analysis unavailable</b><span>{error}</span></div>}
        {busy && <Progress steps={progress} />}
      </section>

      {caseData && <Results caseData={caseData} form={form} copyWallet={copyWallet} copyState={copyState} monitor={monitor} />}
    </main>
  )
}

function Field({ label, hint, className = '', children }: { label: string; hint?: string; className?: string; children: React.ReactNode }) {
  return <div className={`field ${className}`}><span>{label}{hint && <em>{hint}</em>}</span>{children}</div>
}

function Progress({ steps }: { steps: ProgressKey[] }) {
  return <div className="progress" aria-live="polite"><div className="progressHeader"><b>Analysis progress</b><span>{steps.length}/{progressSteps.length} complete</span></div><div className="progressSteps">{progressSteps.map(step => <div className={steps.includes(step.key) ? 'done' : ''} key={step.key}><span>{steps.includes(step.key) ? '✓' : '○'}</span>{step.label}</div>)}</div></div>
}

function Results({ caseData, form, copyWallet, copyState, monitor }: { caseData: CaseRecord; form: { wallet_address: string }; copyWallet: () => void; copyState: string; monitor: () => void }) {
  const networkLabel = networkOptions.find(option => option.value === caseData.input.blockchain)?.label || caseData.input.blockchain
  const incoming = caseData.transactions.filter(tx => tx.to_address.toLowerCase() === form.wallet_address.toLowerCase()).length
  const outgoing = caseData.transactions.length - incoming
  const indicatorNames = new Set(caseData.risk.factors.map(factor => factor.name))
  const graph = useMemo(() => ({
    nodes: caseData.nodes.map((node, index) => ({ id: node.id, position: { x: (index % 4) * 220, y: Math.floor(index / 4) * 150 }, data: { label: `${node.node_type === 'exchange' ? 'VASP / ' : ''}${node.label}` }, className: `graphNode ${node.node_type}`, style: { padding: 10, borderRadius: 8, width: 180, fontSize: 12 } })),
    edges: caseData.edges.map(edge => ({ id: edge.id, source: edge.source, target: edge.target, label: `${Number(edge.amount).toLocaleString()} ${edge.asset}`, markerEnd: { type: MarkerType.ArrowClosed }, style: { strokeWidth: 2 } })),
  }), [caseData])

  return <div className="results" id="results">
    <div className="resultsHeader"><div><div className="sectionKicker">CASE {caseData.id}</div><h2>Investigation Results</h2><p>DEMO ANALYSIS <span className="muted">·</span> Network: <strong>{networkLabel}</strong></p></div><a className="secondaryButton" href={`${API}/api/cases/${caseData.id}/report`} target="_blank" rel="noreferrer">Export PDF report</a></div>
    <section className="summaryGrid"><div className="panel walletSummary"><PanelHeading eyebrow="WALLET ANALYSIS" title="Suspect wallet" /><div className="addressRow"><code title={form.wallet_address}>{form.wallet_address}</code><button className="tinyButton" onClick={copyWallet}>{copyState}</button></div><div className="detailGrid"><Detail label="Network" value={networkLabel} /><Detail label="Wallet type" value="Unknown" /><Detail label="Transactions" value={String(caseData.transactions.length)} /><Detail label="Trace depth" value={`${caseData.max_hop_depth} hops`} /></div><div className="demoNotice">Synthetic trace generated by the local demo blockchain provider. Address attribution is not proof of criminal activity.</div></div><div className={`panel scoreCard ${caseData.risk.level.toLowerCase()}`}><PanelHeading eyebrow="RISK ASSESSMENT" title="Investigative priority" /><div className="score"><strong>{caseData.risk.score}</strong><span>/100</span></div><div className="riskLabel"><b>{caseData.risk.level.toUpperCase()} PRIORITY</b><span>Risk indicators, not a legal conclusion</span></div><div className="factorList">{caseData.risk.factors.map(factor => <div className="factor" key={factor.name}><b>+{factor.points}</b><span><strong>{factor.name}</strong><small>{factor.evidence}</small></span></div>)}</div></div></section>
    <section className="panel graphPanel"><PanelHeading eyebrow="FUND FLOW" title="Transaction graph" description="Directed flow through reported and connected wallets." /><div className="flow"><ReactFlow nodes={graph.nodes} edges={graph.edges} fitView><Background color="#26384d" gap={28} /><Controls /></ReactFlow></div><div className="legend"><span><i className="reported" />Reported wallet</span><span><i className="wallet" />Intermediary</span><span><i className="exchange" />Possible VASP association</span></div><div className="evidenceNote"><b>Entity evidence:</b> {caseData.entities[0] ? `${caseData.entities[0].entity_name}, ${caseData.entities[0].confidence}% confidence, ${caseData.entities[0].source}.` : 'VASP association not established.'}</div></section>
    <section className="summaryGrid"><div className="panel"><PanelHeading eyebrow="TRANSACTION SUMMARY" title="Trace metrics" /><div className="metricGrid"><Metric label="Total transactions" value={caseData.transactions.length} /><Metric label="Incoming" value={incoming} /><Metric label="Outgoing" value={outgoing} /><Metric label="Total value traced" value={`${Number(caseData.traced_amount).toLocaleString()} ${caseData.input.token}`} /><Metric label="Intermediary wallets" value={Math.max(caseData.nodes.length - caseData.entities.length, 0)} /><Metric label="Maximum depth" value={`${caseData.max_hop_depth} hops`} /></div></div><div className="panel"><PanelHeading eyebrow="SUSPICIOUS INDICATORS" title="Evidence review" /><div className="indicatorTable"><Indicator name="Rapid fund movement" active={indicatorNames.has('Rapid fund movement')} evidence="Sequential transfers occurred within 60 seconds." severity="High" /><Indicator name="Fund fragmentation" active={indicatorNames.has('Fund fragmentation')} evidence="One wallet sent funds to multiple destinations." severity="Medium" /><Indicator name="Known entity connection" active={indicatorNames.has('Known entity connection')} evidence="A labeled entity appears in the trace." severity="Medium" /></div></div></section>
    <section className="twoCol"><div className="panel"><PanelHeading eyebrow="REAL-TIME MONITORING" title="Alert watch" description="Simulates one new event for this demo case." /><button className="primaryButton" onClick={monitor} disabled={caseData.monitoring}>{caseData.monitoring ? 'Monitoring active' : 'Start monitoring'} <span>→</span></button>{caseData.alerts?.map(alert => <div className="alert" key={alert.id}><strong>{alert.severity}-RISK TRANSACTION</strong><span>{Number(alert.amount).toLocaleString()} {alert.asset}</span><small>{alert.reason}</small></div>)}</div><div className="panel"><PanelHeading eyebrow="TRANSACTION TIMELINE" title="Latest trace events" />{caseData.transactions.slice(0, 6).map(tx => <div className="tx" key={tx.tx_hash}><time>{new Date(tx.timestamp).toLocaleTimeString()}</time><code title={tx.from_address}>{tx.from_address.slice(0, 8)}...</code><span>→</span><code title={tx.to_address}>{tx.to_address.slice(0, 8)}...</code><b>{Number(tx.amount).toLocaleString()} {tx.asset}</b></div>)}</div></section>
  </div>
}

function PanelHeading({ eyebrow, title, description }: { eyebrow: string; title: string; description?: string }) { return <div className="panelHeading"><div><div className="sectionKicker">{eyebrow}</div><h3>{title}</h3>{description && <p>{description}</p>}</div></div> }
function Detail({ label, value }: { label: string; value: string }) { return <div className="detail"><span>{label}</span><b>{value}</b></div> }
function Metric({ label, value }: { label: string; value: string | number }) { return <div className="metric"><span>{label}</span><strong>{value}</strong></div> }
function Indicator({ name, active, evidence, severity }: { name: string; active: boolean; evidence: string; severity: string }) { return <div className="indicator"><strong>{name}</strong><span className={active ? 'detected' : 'notDetected'}>{active ? 'Detected' : 'Not detected'}</span><small>{evidence}</small><b>{active ? severity : 'Low'}</b></div> }
