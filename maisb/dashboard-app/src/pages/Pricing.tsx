import PricingCard from '../components/PricingCard'

export default function Pricing() {
  return <main className="page"><h1>Pricing</h1><div className="grid"><PricingCard title="Free Developer" price="$0" points={["Prompt-injection scanning", "Community support"]} /><PricingCard title="Pro" price="Paid plan" points={["Higher quota", "Email support"]} /><PricingCard title="Enterprise" price="Custom" points={["SOC workflows", "Private support"]} /><PricingCard title="MAISB Certify" price="Assessment" points={["Report PDF", "Badge verification"]} /></div></main>
}
