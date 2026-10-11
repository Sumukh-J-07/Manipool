import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootParams } from './types';
import { RideRequest } from '../types/domain';
export function goMain(
  navigation: Pick<NativeStackNavigationProp<RootParams>, 'reset'>,
  screen: 'Home' | 'Rides' | 'Profile' = 'Home',
) {
  navigation.reset({
    index: 0,
    routes: [{ name: 'Main', params: { screen } }],
  });
}
export function openRide(
  navigation: Pick<NativeStackNavigationProp<RootParams>, 'navigate'>,
  ride: RideRequest,
) {
  const params = { rideId: ride.id };
  switch (ride.status) {
    case 'SEARCHING':
    case 'REMATCHING':
      navigation.navigate('Matching', params);
      break;
    case 'MATCH_FOUND':
    case 'NO_MATCH':
      navigation.navigate('Results', params);
      break;
    case 'WAITING_FOR_ACCEPTANCE':
      navigation.navigate('MatchDetails', params);
      break;
    case 'GROUP_FORMED':
      navigation.navigate('GroupRide', params);
      break;
    case 'RIDE_BOOKED':
    case 'IN_PROGRESS':
      navigation.navigate('ActiveRide', params);
      break;
    case 'COMPLETED':
      navigation.navigate('Completed', params);
      break;
    default:
      navigation.navigate('RideDetails', params);
  }
}
