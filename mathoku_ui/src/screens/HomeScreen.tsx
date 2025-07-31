import React, { useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, Button } from 'react-native';
import MathokuNative from '../native/MathokuNative';
import { User } from '../types/backend';

// Minimal course type definition
interface Course {
  id: string;
  title: string;
}

// Dummy data for now
const courses: Course[] = [
  { id: '1', title: 'Binary Search' },
  { id: '2', title: 'Depth-First Search' },
  { id: '3', title: 'Dijkstra\'s Algorithm' },
];

interface HomeScreenProps {
  navigation: any;
}

export default function HomeScreen({ navigation }: HomeScreenProps) {
  const [user, setUser] = React.useState<User | undefined>(undefined);

  console.log('HomeScreen rendered');

  React.useEffect(() => {
    const fetchData = async () => {
      console.log('Fetching dummy user JSON from native module...');
      
      const json = await MathokuNative.getDummyUserJson();

      console.log('Dummy User JSON:', json);

      const user: User = JSON.parse(json);

      setUser(user);
    };

    fetchData();
  }, []);

  const showAlert = () => {
    Alert.alert('This is a dummy alert!');
  };

  const renderItem = ({ item }: { item: Course }) => (
    <TouchableOpacity
      style={styles.item}
      onPress={() => navigation.navigate('CourseDetail', { courseId: item.id })}
    >
      <Text style={styles.title}>{item.title}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text>Welcome to Mathoku!</Text>
      {user && (
        <Text>
          Dummy User: {user.name} ({user.email})
        </Text>
      )}
      <FlatList
        data={courses}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
      />
      <Button title="Show Alert" onPress={showAlert} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  item: { padding: 12, marginBottom: 8, backgroundColor: '#eee', borderRadius: 4 },
  title: { fontSize: 18 },
});
