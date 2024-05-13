# Clean Archtecture
## Domain
1. Onde ficam as regras de negócio
2. Não tem implementações de classes, apenas classes abstratas e entidades

## Data Layer 
1. Onde ficam as classes concretas definidas na camada de domínio (domain)
2. Onde são aplicadas as regras de negócio
3. Essa camada também define abstrações de serviços que precisa consumir que serão implementados na camada de infrestrutura 

## Infra
1. Onde ficam chamadas de funções/bibliotecas de terceiros ou APIs
2. Sua importância é assegurar uma interface à camada de dados, mesmo que as funções ou bibliotecas chamadas se alterem

## Main layer
fica aclopado a todas as camadas (tem conhecimento de todas) para que seja possível desacoplar as demais

## Observações
Camadas externas acessam camadas internas, mas camanas internas não acessam camadas externas. Isso significa que Data Layer pode importar algo de Domain, mas nunca o inverso.


# Project definitions

## /app
### /app/use_cases 
must implent the code logic, which means it must have an usecase that receives an image and coordinates. So it will drawn this coordinates over the image and return it. These must be abstract class inputed as attributes or injections in the use_case.

In other words, an use_case class may look like

        class UseCase
            # atributtes
            service1 of type AbstractService1
            service2 of type AbstractService2
        end

The reason for that is that there are many ways of generating an image and getting coordinates and these are services that use_cases shouldn't worry about it.

### /app/services 
Where the services abstract class must be stored

## /infra 
Must implement the services defined at /app/services

## How it should work
The use case must be build somewhere. It may be a PRESENTATION LAYER, if the intetion is to build the whole application, or in another application, if the intetion is to build an library.

Anyway, the point here is that the use_case implemented at app layer must be build somewhere, receiving the services (and any abstract class needed) as attributes. It may look like:

        use_case = new UseCase(service1, service2)

## Observations
The rules implemented in the app/use_cases may be defined in a layer named domain, in the /domain/use_cases. We are just not doin it at the moment