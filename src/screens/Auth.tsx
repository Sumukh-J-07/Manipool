import React, { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootParams } from '../navigation/types';
import {
  Button,
  Copy,
  ErrorText,
  Input,
  Kicker,
  Page,
  Title,
} from '../components/ui';
import { RouteLogo, RouteMap } from '../components/RouteMap';
import { useApp } from '../state/AppContext';
import { demoProfile } from '../data/fixtures';
export function WelcomeScreen({
  navigation,
}: NativeStackScreenProps<RootParams, 'Welcome'>) {
  return (
    <Page>
      <View style={styles.brand}>
        <RouteLogo />
        <Kicker>MAHE Carpool</Kicker>
      </View>
      <View style={styles.space} />
      <Kicker>Different routes. One journey.</Kicker>
      <Title>Share the journey,{'\n'}not just the ride.</Title>
      <Copy muted>
        Connect with MAHE students travelling your way. Find your people, agree
        a pickup, and share the fare.
      </Copy>
      <RouteMap start="Individual journeys" end="One shared route" />
      <Button
        label="Get Started"
        onPress={() => navigation.navigate('Login')}
      />
      <Button
        secondary
        label="Continue as Demo"
        onPress={() => navigation.navigate('Setup')}
      />
      <Copy small muted>
        A campus mobility prototype. All riders, messages and bookings are
        simulated.
      </Copy>
    </Page>
  );
}
export function LoginScreen({
  navigation,
}: NativeStackScreenProps<RootParams, 'Login'>) {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const next = () => {
    if (!/^[^\s@]+@(?:learner\.)?manipal\.edu$/i.test(email.trim())) {
      setError('Use a MAHE-style email such as name@learner.manipal.edu.');
      return;
    }
    navigation.navigate('Setup', { email: email.trim() });
  };
  return (
    <Page back>
      <RouteLogo />
      <Kicker>Built for the MAHE community</Kicker>
      <Title>A familiar place.{'\n'}A shared way home.</Title>
      <Copy muted>
        Enter a student email to personalise your local demo. No verification
        email or OTP is sent.
      </Copy>
      <Input
        label="MAHE email · demo only"
        placeholder="name@learner.manipal.edu"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <ErrorText message={error} />
      <Button label="Continue" onPress={next} />
      <Button
        secondary
        label="Use demo profile"
        onPress={() => navigation.navigate('Setup')}
      />
    </Page>
  );
}
export function SetupScreen({
  route,
}: NativeStackScreenProps<RootParams, 'Setup'>) {
  const { state, dispatch } = useApp();
  const [name, setName] = useState(demoProfile.name);
  const [email, setEmail] = useState(route.params?.email ?? demoProfile.email);
  return (
    <Page back>
      <Kicker>Make yourself at home</Kicker>
      <Title>Your demo profile</Title>
      <Copy muted>
        These details stay in this app session. This is a demo identity, with no
        verified student status.
      </Copy>
      <Input
        label="Student name"
        value={name}
        onChangeText={setName}
        maxLength={60}
      />
      <Input
        label="Demo MAHE email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <ErrorText message={state.error} />
      <Button
        label="Start sharing journeys"
        onPress={() =>
          dispatch({
            type: 'SIGN_IN',
            profile: { ...demoProfile, name, email: email.trim() },
          })
        }
      />
    </Page>
  );
}
const styles = StyleSheet.create({
  brand: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  space: { height: 28 },
});
