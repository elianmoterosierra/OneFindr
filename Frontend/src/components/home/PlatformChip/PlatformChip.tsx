import { Icon } from '../../Icon/Icon'
import './PlatformChip.css'

type PlatformChipProps = {
  name: string
  checked: boolean
  onChange: () => void
}

export function PlatformChip({ name, checked, onChange }: PlatformChipProps) {
  return (
    <label className={`platform-chip ${checked ? 'checked' : ''}`}>
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span className="chip-icon">
        {checked ? <Icon name="check" size={12} /> : <span className="empty-dot" />}
      </span>
      <span>{name}</span>
    </label>
  )
}
