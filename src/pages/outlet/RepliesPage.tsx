import { NavLink } from 'react-router-dom'
import { ReplyQueue } from '../../components/Panels'
import { SectionHead } from '../../components/Page'
import { useOutlet } from './OutletLayout'

export default function RepliesPage() {
  const { id } = useOutlet()
  return (
    <div className="space-y-5">
      <SectionHead
        title="Replies"
        sub="A drafted reply for every unanswered negative review. Edit, shorten or regenerate it, then approve. Nothing is posted until you do."
        action={<NavLink to="/tone" className="btn !py-1.5 !text-xs">Change reply tone</NavLink>}
      />
      <div className="max-w-3xl"><ReplyQueue id={id} /></div>
    </div>
  )
}
