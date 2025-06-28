import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  //docker has 5050
  
  await app.listen(5050);
}
bootstrap();
