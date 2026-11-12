import { Icon } from '../../Icon/Icon'
import './PlatformChip.css'
import { useSources } from '../../../store/useSource'

type PlatformChipProps = {
  sourceKey: string
  name: string
  active: boolean
}

export function PlatformChip({ sourceKey, name, active }: PlatformChipProps) {
  const { toggleSource } = useSources()

  return (
    <button
      type="button"
      className={`platform-chip ${active ? 'checked' : ''}`}
      onClick={() => toggleSource(sourceKey)}
      aria-pressed={active}
    >
      <span className="chip-icon">
        {active ? <Icon name="check" size={12} /> : <span className="empty-dot" />}
      </span>
      <span>{name}</span>
    </button>
  )
}
