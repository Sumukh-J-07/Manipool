/**
 * @format
 */

import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import { Alert } from 'react-native';
import App from '../App';

test('launches through splash to the welcome screen', async () => {
  jest.useFakeTimers();
  let renderer: ReactTestRenderer.ReactTestRenderer;
  await ReactTestRenderer.act(async () => {
    renderer = ReactTestRenderer.create(<App />);
  });
  await ReactTestRenderer.act(async () => {
    jest.advanceTimersByTime(600);
  });
  expect(
    renderer!.root.findAllByProps({ accessibilityLabel: 'Continue as Demo' })
      .length,
  ).toBeGreaterThan(0);
  await ReactTestRenderer.act(async () => {
    renderer!.unmount();
  });
  jest.useRealTimers();
});

test('connects demo onboarding, matching, acceptance, booking and completion to history', async () => {
  jest.useFakeTimers();
  const alert = jest
    .spyOn(Alert, 'alert')
    .mockImplementation((_title, _message, buttons) => {
      buttons?.find(button => button.text === 'Confirm demo')?.onPress?.();
    });
  let renderer: ReactTestRenderer.ReactTestRenderer;
  await ReactTestRenderer.act(async () => {
    renderer = ReactTestRenderer.create(<App />);
  });
  const press = async (label: string) => {
    const buttons = renderer!.root.findAll(
      node =>
        node.props.accessibilityLabel === label &&
        typeof node.props.onPress === 'function',
    );
    expect(buttons.length).toBeGreaterThan(0);
    await ReactTestRenderer.act(async () => {
      buttons[buttons.length - 1].props.onPress();
    });
    await ReactTestRenderer.act(async () => {
      jest.advanceTimersByTime(350);
    });
  };
  await ReactTestRenderer.act(async () => {
    jest.advanceTimersByTime(600);
  });
  await press('Continue as Demo');
  await press('Start sharing journeys');
  await press('Find a Carpool');
  await ReactTestRenderer.act(async () => {
    jest.advanceTimersByTime(1600);
  });
  await press('View Match');
  await press('Join Carpool');
  await press('Simulate other riders accepting');
  await press('Choose Cab / Auto');
  await press('Confirm simulated booking');
  await press('Start Demo Ride');
  await press('Complete Demo Ride');
  await press('Done · View ride history');
  expect(
    renderer!.root.findAllByProps({ accessibilityLabel: 'View completed ride' })
      .length,
  ).toBeGreaterThan(0);
  await ReactTestRenderer.act(async () => {
    renderer!.unmount();
  });
  alert.mockRestore();
  jest.useRealTimers();
}, 30000);
