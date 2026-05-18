import { useEffect, useState } from 'react'
import PricingCard from '../components/PricingCard'
import { apiRequest } from '../lib/api'

type Plan = { id: string; name: string; price: string; features: string[] }

export default function Pricing() {
  const [plans, setPlans] = useState<Plan[]>([])

  useEffect(() => {
    apiRequest<{ plans: Plan[] }>('/v1/public/plans').then((data) => setPlans(data.plans || []))
  }, [])

  return (
    <main className="public-page">
      <h2>Pricing</h2>
      <div className="grid">
        {plans.map((plan) => (
          <PricingCard key={plan.id} plan={plan} />
        ))}
      </div>
    </main>
  )
}
