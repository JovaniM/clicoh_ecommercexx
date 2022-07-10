# Clicoh Ecommerce Test
This project is a API to get the job as Backend developer on clicoh backend developer position.

This API is used to create Products, Orders following the convention described on the PDF but here we add some extra validations.

- Product can be created just by staff users.
- Product can be available or unavailable.
- Product stock is updated from Orders only.
- We can have INGRESS Orders (to add stock to products) or EGRESS Orders (wich substracts product stock).

The API is secured using JWT token authentication.

## API documentation
You could find the related swagger documentation for API on the route:
- passing by email

## Using the app
You could create normal users using the app signup endpoint or use the existing users:
- Staff user: 
    - email: staff@email.com
    - password: staff_user1234

- Normal user:
    - user: normal@email.com
    - password: normal_user1234