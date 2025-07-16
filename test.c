#include <stdio.h>
int sum(int a, int b) {
    return a + b;
}
int main(void)
{
   int x, y;
   printf("Enter two integers: ");
   if (scanf("%d %d", &x, &y) != 2) {
       printf("Invalid input.\n");
       return 1;
   }
   int result = sum(x, y);
   printf("The sum of %d and %d is %d\n", x, y, result);
   return 0;
}
