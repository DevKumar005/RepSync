import { useQuery } from '@tanstack/react-query'
import { extrasApi } from './api'

/** City map data; keeps polling while the backend is still locating the outlet or its nearby places. */
export function useCityMap(id: string) {
  return useQuery({
    queryKey: ['extras', 'city-map', id],
    queryFn: () => extrasApi.cityMap(id),
    refetchInterval: (q) => (q.state.data?.status === 'locating' || q.state.data?.places_status === 'loading' ? 2500 : false),
  })
}
