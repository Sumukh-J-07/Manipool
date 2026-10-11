import React, { useState } from 'react';
import { Alert, TextInput, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { DateTimePickerAndroid } from '@react-native-community/datetimepicker';
import {
  CalendarDays,
  Clock3,
  MapPin,
  Navigation,
  Plane,
  TrainFront,
} from 'lucide-react-native';
import { RootParams } from '../navigation/types';
import {
  Badge,
  Button,
  Card,
  Choice,
  Copy,
  ErrorText,
  Heading,
  Kicker,
  Page,
  Row,
  Title,
  ui,
} from '../components/ui';
import { RouteLogo, RouteMap } from '../components/RouteMap';
import { RideSummary } from '../components/RideSummary';
import { getLocation, locations } from '../data/fixtures';
import { newId, nowISO, useApp } from '../state/AppContext';
import { departureFromDraft, isOpen, validateDraft } from '../services/journey';
import { openRide } from '../navigation/actions';

export function JourneyForm() {
  const { state, dispatch } = useApp();
  const navigation = useNavigation<NativeStackNavigationProp<RootParams>>();
  const [error, setError] = useState<string>();
  const draft = state.draft;
  const current = state.rides.find(ride => isOpen(ride.status));
  const chooseDate = (mode: 'date' | 'time') =>
    DateTimePickerAndroid.open({
      value: departureFromDraft(draft) ?? new Date(),
      mode,
      is24Hour: false,
      minimumDate: mode === 'date' ? new Date() : undefined,
      onChange: (event, selected) => {
        if (event.type !== 'set' || !selected) {
          return;
        }
        dispatch({
          type: 'DRAFT',
          patch:
            mode === 'date'
              ? {
                  date: `${selected.getFullYear()}-${String(
                    selected.getMonth() + 1,
                  ).padStart(2, '0')}-${String(selected.getDate()).padStart(
                    2,
                    '0',
                  )}`,
                }
              : {
                  time: `${String(selected.getHours()).padStart(
                    2,
                    '0',
                  )}:${String(selected.getMinutes()).padStart(2, '0')}`,
                },
        });
      },
    });
  const find = () => {
    if (current) {
      Alert.alert(
        'One journey at a time',
        'Resume or cancel your existing demo request first.',
        [
          { text: 'Back', style: 'cancel' },
          {
            text: 'Resume journey',
            onPress: () => openRide(navigation, current),
          },
        ],
      );
      return;
    }
    const validation = validateDraft(draft);
    setError(validation);
    if (validation) {
      return;
    }
    const id = newId('ride');
    dispatch({ type: 'SEARCH', id, now: nowISO() });
    navigation.navigate('Matching', { rideId: id });
  };
  return (
    <Card>
      <Choice
        icon={MapPin}
        label={getLocation(draft.pickupId)?.name ?? 'Choose pickup'}
        detail="Pickup · demo landmark"
        onPress={() =>
          navigation.navigate('LocationSearch', { field: 'pickupId' })
        }
      />
      <Choice
        icon={Navigation}
        label={getLocation(draft.destinationId)?.name ?? 'Choose destination'}
        detail="Where are you headed?"
        onPress={() =>
          navigation.navigate('LocationSearch', { field: 'destinationId' })
        }
      />
      <Row>
        <View style={ui.flex}>
          <Choice
            icon={CalendarDays}
            label={draft.date}
            detail="Departure date"
            onPress={() => chooseDate('date')}
          />
        </View>
        <View style={ui.flex}>
          <Choice
            icon={Clock3}
            label={draft.time}
            detail="Departure time"
            onPress={() => chooseDate('time')}
          />
        </View>
      </Row>
      <Copy small>Time flexibility</Copy>
      <Row wrap>
        {([0, 15, 30, 45] as const).map(minutes => (
          <Choice
            key={minutes}
            label={minutes ? `±${minutes} min` : 'Exact time'}
            selected={draft.flexibility === minutes}
            onPress={() =>
              dispatch({ type: 'DRAFT', patch: { flexibility: minutes } })
            }
          />
        ))}
      </Row>
      <ErrorText message={error ?? state.error} />
      <Button label="Find a Carpool" onPress={find} />
      <Button
        secondary
        label="Preview the route"
        onPress={() => navigation.navigate('MapPreview')}
      />
    </Card>
  );
}
export function HomeScreen() {
  const { state, dispatch } = useApp();
  const navigation = useNavigation<NativeStackNavigationProp<RootParams>>();
  const upcoming = state.rides.find(ride =>
    ['GROUP_FORMED', 'RIDE_BOOKED', 'IN_PROGRESS'].includes(ride.status),
  );
  return (
    <Page>
      <View style={ui.spread}>
        <RouteLogo />
        <Badge>Campus demo</Badge>
      </View>
      <Kicker>Hello, {state.profile.name.split(' ')[0]}</Kicker>
      <Title>Where are{'\n'}you going?</Title>
      <Copy muted>
        Different routes. One journey.{'\n'}Ready to share a ride?
      </Copy>
      <JourneyForm />
      <Heading>Campus favourites</Heading>
      <Row wrap>
        {locations
          .filter(location =>
            ['airport', 'metro', 'railway'].includes(location.id),
          )
          .map(location => (
            <Choice
              key={location.id}
              icon={location.kind === 'airport' ? Plane : TrainFront}
              label={location.name}
              onPress={() =>
                dispatch({
                  type: 'DRAFT',
                  patch: { destinationId: location.id },
                })
              }
            />
          ))}
      </Row>
      {upcoming && (
        <>
          <Heading>Your upcoming journey</Heading>
          <RideSummary
            ride={upcoming}
            group={state.groups.find(group => group.id === upcoming.groupId)}
          />
          <Button
            secondary
            label="Resume journey"
            onPress={() => openRide(navigation, upcoming)}
          />
        </>
      )}
      <Copy small muted>
        Sample people, locations and estimates. No live location or provider
        connection.
      </Copy>
    </Page>
  );
}
export function CreateRideScreen() {
  return (
    <Page back>
      <Kicker>A journey worth sharing</Kicker>
      <Title>Plan your ride</Title>
      <Copy muted>
        Choose landmarks and a departure window that works for you.
      </Copy>
      <JourneyForm />
    </Page>
  );
}
export function LocationSearchScreen({
  route,
}: import('@react-navigation/native-stack').NativeStackScreenProps<
  RootParams,
  'LocationSearch'
>) {
  const { state, dispatch } = useApp();
  const navigation = useNavigation<NativeStackNavigationProp<RootParams>>();
  const [query, setQuery] = useState('');
  const options = locations.filter(
    location =>
      (!route.params.savedOnly || state.savedPlaces.includes(location.id)) &&
      `${location.name} ${location.area}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  return (
    <Page back>
      <Kicker>Demo landmarks</Kicker>
      <Title>
        {route.params.savedOnly
          ? 'Saved places'
          : route.params.field === 'pickupId'
          ? 'Choose your pickup'
          : 'Choose a destination'}
      </Title>
      <Copy muted>
        Search our local sample list. No GPS or geocoding permissions needed.
      </Copy>
      <TextInput
        accessibilityLabel="Search demo locations"
        placeholder="Search campus, airport, metro…"
        value={query}
        onChangeText={setQuery}
        style={{ ...uiInput }}
        placeholderTextColor={inputColors.secondary}
      />
      <Button
        secondary
        label="Use demo current location: campus"
        onPress={() => {
          dispatch({
            type: 'DRAFT',
            patch: { [route.params.field]: 'campus' },
          });
          navigation.goBack();
        }}
      />
      {options.map(location => (
        <Card key={location.id}>
          <Choice
            icon={MapPin}
            label={location.name}
            detail={location.area}
            selected={state.draft[route.params.field] === location.id}
            onPress={() => {
              dispatch({
                type: 'DRAFT',
                patch: { [route.params.field]: location.id },
              });
              navigation.goBack();
            }}
          />
          <Button
            secondary
            label={
              state.savedPlaces.includes(location.id)
                ? 'Remove from saved places'
                : 'Save this place'
            }
            onPress={() => dispatch({ type: 'SAVE', locationId: location.id })}
          />
        </Card>
      ))}
      {!options.length && (
        <Copy muted>
          No demo places found. Try a broader search or save a place from the
          full list.
        </Copy>
      )}
      <Button
        secondary
        label="View selected route"
        onPress={() => navigation.navigate('MapPreview')}
      />
    </Page>
  );
}
import { colors as inputColors } from '../theme';
const uiInput = {
  minHeight: 54,
  borderWidth: 1,
  borderColor: inputColors.border,
  borderRadius: 14,
  padding: 16,
  backgroundColor: inputColors.surface,
  color: inputColors.text,
  fontSize: 16,
};
export function MapPreviewScreen() {
  const { state } = useApp();
  const navigation = useNavigation<NativeStackNavigationProp<RootParams>>();
  return (
    <Page back>
      <Kicker>Connected routes</Kicker>
      <Title>Your journey,{'\n'}in perspective.</Title>
      <RouteMap
        start={getLocation(state.draft.pickupId)?.name}
        end={getLocation(state.draft.destinationId)?.name}
      />
      <Copy muted>
        This illustration shows the idea of converging pickups. It is not a
        navigable map or a measured road route.
      </Copy>
      <Button
        secondary
        label="Change pickup"
        onPress={() =>
          navigation.navigate('LocationSearch', { field: 'pickupId' })
        }
      />
      <Button
        secondary
        label="Change destination"
        onPress={() =>
          navigation.navigate('LocationSearch', { field: 'destinationId' })
        }
      />
      <Button
        label="Return to journey form"
        onPress={() =>
          navigation.reset({
            index: 0,
            routes: [{ name: 'Main', params: { screen: 'Home' } }],
          })
        }
      />
    </Page>
  );
}
