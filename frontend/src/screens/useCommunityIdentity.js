import { useEffect, useState } from 'react'

function makeNeighborName() {
  return `Neighbor #${Math.floor(100 + Math.random() * 900)}`
}

function addressNickname(label) {
  const street = label.split(',')[0].trim().replace(/\s+\d+\S*$/, '')
  return street ? `Resident on ${street}` : ''
}

export function useCommunityIdentity(home = null) {
  const [neighborName] = useState(() => {
    const saved = localStorage.getItem('community_neighbor')
    if (saved) return saved
    const generated = makeNeighborName()
    localStorage.setItem('community_neighbor', generated)
    return generated
  })
  const name = home?.label ? addressNickname(home.label) || neighborName : neighborName

  useEffect(() => {
    localStorage.setItem('community_neighbor', neighborName)
    localStorage.setItem('community_user', name)
  }, [name, neighborName])

  return name
}
