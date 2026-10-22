import './Icon.css'

type IconName =
  | 'arrow'
  | 'arrow-outward'
  | 'check'
  | 'close'
  | 'favorite'
  | 'filter'
  | 'insights'
  | 'magnifying-glass'
  | 'notification'
  | 'person-pin'
  | 'search'
  | 'shield'
  | 'star'
  | 'storefront'
  | 'tune'
  | 'user'

type IconProps = {
  name: IconName
  size?: number
}

const materialIconNames: Record<IconName, string> = {
  arrow: 'arrow_forward',
  'arrow-outward': 'arrow_outward',
  check: 'check',
  close: 'close',
  favorite: 'favorite',
  filter: 'tune',
  insights: 'insights',
  'magnifying-glass': 'search',
  notification: 'notifications_active',
  'person-pin': 'person_pin_circle',
  search: 'search',
  shield: 'verified_user',
  star: 'star',
  storefront: 'storefront',
  tune: 'tune',
  user: 'person',
}

export function Icon({ name, size = 18 }: IconProps) {
  return (
    <span
      className="material-symbols-outlined icon"
      style={{ fontSize: size }}
      aria-hidden="true"
    >
      {materialIconNames[name]}
    </span>
  )
}
