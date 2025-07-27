import React, { useState } from 'react';
import { SafeAreaView, Button, Text, StyleSheet } from 'react-native';
import MathokuNative from './src/native/MathokuNative';

export default function App() {
  const [message, setMessage] = useState<string>('no message yet');

  const onPress = async () => {
    try {
      const result = await MathokuNative.greet('React User');
      setMessage(result);
    } catch (err: any) {
      console.error(err);
      setMessage('Error: ' + (err.message || JSON.stringify(err)));
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Button title="Say Hello from Rust!" onPress={onPress} />
      <Text style={styles.text}>{message}</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  text: { marginTop: 20, fontSize: 18 },
});